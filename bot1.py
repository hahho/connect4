from basics import *
import numpy as np
import utils

dlist = [(1,1),(1,0),(0,1),(1,-1)]

class NPBoard(Board):
	def __init__(self, starting_board = False):
		super().__init__(starting_board)
		if starting_board:
			self._board = np.zeros((W,H), dtype='int8')
			self._next_empty_y = np.zeros(W, dtype='int8')
			self.score = 0
			self.hash = utils.START_HASH

	
	def next_boards(self, color):
		for x in range(W):
			if self[x,H-1] == 0:
				yield self.make_move(x, color)

	def next_board_hashes(self, color):
		for x in range(W):
			y = int(self._next_empty_y[x])
			if y < H:
				h = utils.move_hash(self.hash, color, x, y)
				yield (h, x)

	def make_move(self, x, color):
		y = int(self._next_empty_y[x])

		nboard = NPBoard()
		nboard._board = np.copy(self._board)
		nboard._next_empty_y = np.copy(self._next_empty_y)
		nboard.last_move = x

		nboard.hash = utils.move_hash(self.hash, color, x, y)
		nboard[x,y] = color
		nboard._next_empty_y[x] += 1
		
		dscore = 3 - abs(x-3)

		for dx,dy in dlist:
			s1 = 0
			nx, ny = x+dx,y+dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and nboard[nx,ny] == color:
				s1 += 1
				nx += dx
				ny += dy

			s2 = 0
			nx, ny = x-dx,y-dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and nboard[nx,ny] == color:
				s2 += 1
				nx -= dx
				ny -= dy

			dscore += CHAIN_SCORE[s1+s2+1] - CHAIN_SCORE[s1] - CHAIN_SCORE[s2]

		nboard.score = self.score + dscore*color


		return nboard

	def Dmake_move(self, x, color, nhash):
		y = int(self._next_empty_y[x])

		self.hash = nhash
		self[x,y] = color
		self._next_empty_y[x] += 1
		
		dscore = 3 - abs(x-3)

		for dx,dy in dlist:
			s1 = 0
			nx, ny = x+dx,y+dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and self[nx,ny] == color:
				s1 += 1
				nx += dx
				ny += dy

			s2 = 0
			nx, ny = x-dx,y-dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and self[nx,ny] == color:
				s2 += 1
				nx -= dx
				ny -= dy

			dscore += CHAIN_SCORE[s1+s2+1] - CHAIN_SCORE[s1] - CHAIN_SCORE[s2]

		self.score += dscore*color

	def revert(self, x, h, score):
		y = self._next_empty_y[x]-1
		self._next_empty_y[x] = y

		self._board[x,y] = 0
		self.hash = h
		self.score = score

	@property
	def status(self):
		if abs(self.score) > END_INT:
			return FIRST_WIN if self.score > 0 else SECOND_WIN
		if all(self[x,H-1] != 0 for x in range(W)):
			return DRAW
		return IN_PROGRESS


	def __getitem__(self, key):
		return int(self._board[key])

	def __setitem__(self, key, item):
		self._board[key] = item

	def __lt__(self, other):
		return False


END_INT = 50000
CHAIN_SCORE = [0, 0, 100, 300, 100000, 100000, 100000, 100000]



class Aegis(Bot):
	def __init__(self, turn, depth=6, time=None, debug=False, quiet=False):
		super().__init__(turn)
		self.depth = depth
		self.time = time
		self.debug = debug
		self.table = utils.HashTable()
		self.board = None
		self.quiet = quiet

	def generate_move(self, board):
		if self.quiet:
			self.table.shrink_table(board.hash)
		else:
			print('current table size =',len(self.table))
			self.table.shrink_table(board.hash)
			print('table shrunk, now the size =', len(self.table))


		searched_depth = self.table[board][0]

		self.board = board
		for d in range(searched_depth+1, self.depth):
			self.nega_alpha(self.turn, d, -END_INT*10, +END_INT*10)
		ev = self.nega_alpha(self.turn, self.depth, -END_INT*10, +END_INT*10)

		pv = []
		t = self.turn
		for d in range(self.depth):
			try:
				board = max((self.table[b], b) for b in board.next_boards(t))[1]
				pv.append(board)
				if abs(board.score) > END_INT:
					break
			except ValueError:
				break
			t *= -1

		return ev, pv

	def generate_move_for_learning(self, board):
		searched_depth = self.table[board][0]

		self.board = board
		for d in range(searched_depth+1, self.depth):
			self.nega_alpha(self.turn, d, -END_INT*10, +END_INT*10)
		ev = self.nega_alpha(self.turn, self.depth, -END_INT*10, +END_INT*10)


		best = max((self.table[h],h,x) for h,x in self.board.next_board_hashes(self.turn))

		board.Dmake_move(best[2],self.turn,best[1])
		return ev, board

	def nega_alpha(self, turn, depth, alpha, beta):

		if abs(self.board.score) > END_INT:
			self.table[self.board] = (100, END_INT + depth)
			return -END_INT - depth

		if depth <= 0:
			s = self.board.score*turn
			self.table[self.board] = (depth, -s)
			return s

		child_info = [(self.table[h], h, x) for h,x in self.board.next_board_hashes(turn)]

		if not child_info:
			self.table[self.board] = (0, 0)
			return 0

		child_info.sort(reverse=True)

		original_score = self.board.score
		original_hash = self.board.hash

		best = None
		for _, h, x in child_info:

			self.board.Dmake_move(x, turn, h)
			score = -self.nega_alpha(-turn, depth-1,-beta,-alpha)
			self.board.revert(x, original_hash, original_score)

			if alpha < score:
				alpha = score
				best = h
				if alpha >= beta:
					break

		if best:
			self.table[best] = (self.table[best][0], self.table[best][1]+1)

		self.table[self.board] = (depth, -alpha)
		return alpha