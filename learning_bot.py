from basics import *
import numpy as np
import utils


INF = 100000

class LBoard(Board):
	def __init__(self, starting_board = False ):
		super().__init__(starting_board)
		if starting_board:
			self._board = np.zeros((W,H), dtype='int8')
			self._next_empty_y = np.zeros(W, dtype='int8')
			self.hash = utils.START_HASH
			self.status = 0

	
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

		nboard = LBoard()
		nboard._board = np.copy(self._board)
		nboard._next_empty_y = np.copy(self._next_empty_y)
		nboard.last_move = x

		nboard.hash = utils.move_hash(self.hash, color, x, y)
		nboard[x,y] = color
		nboard._next_empty_y[x] += 1

		

		for dx,dy in [(1,0),(1,1),(0,1),(-1,1)]:
			l = 1
			nx, ny = x+dx,y+dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and nboard[nx,ny] == color:
				l += 1
				nx += dx
				ny += dy

			nx, ny = x-dx,y-dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and nboard[nx,ny] == color:
				l += 1
				nx -= dx
				ny -= dy
			if l >= 4:
				nboard.status = FIRST_WIN if color == 1 else SECOND_WIN
				break
		else:
			nboard.status = IN_PROGRESS

		if y == H-1 and all(nboard[x,H-1] != 0 for x in range(W)):
			nboard.status = DRAW
		return nboard

	def Dmake_move(self, x, color, nhash):
		y = int(self._next_empty_y[x])

		self.hash = nhash
		self[x,y] = color
		self._next_empty_y[x] += 1
		
		for dx,dy in [(1,0),(1,1),(0,1),(-1,1)]:
			l = 1
			nx, ny = x+dx,y+dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and self[nx,ny] == color:
				l += 1
				nx += dx
				ny += dy

			nx, ny = x-dx,y-dy
			while nx >= 0 and nx < W and ny >= 0 and ny < H and self[nx,ny] == color:
				l += 1
				nx -= dx
				ny -= dy
			if l >= 4:
				self.status = color
				break
		else:
			self.status = 0

		if y == H-1 and all(self[x,H-1] != 0 for x in range(W)):
			self.status = DRAW

	def revert(self, x, h):
		y = self._next_empty_y[x]-1
		self._next_empty_y[x] = y

		self._board[x,y] = 0
		self.hash = h
		self.status = 0


	def __getitem__(self, key):
		return int(self._board[key])

	def __setitem__(self, key, item):
		self._board[key] = item

	def __lt__(self, other):
		return False


class LearningBot(Bot):
	def __init__(self, turn, model, depth=6, time=None, debug=False, quiet=False):
		super().__init__(turn)
		self.depth = depth
		self.time = time
		self.debug = debug
		self.table = utils.HashTable()
		self.board = None
		self.model = model
		self.quiet = quiet

	def generate_move(self, board):
		print('current table size =',len(self.table))
		self.table.shrink_table(board.hash)
		print('table shrunk, now the size =', len(self.table))


		searched_depth = self.table.depth(board)

		self.board = board
		for d in range(searched_depth+1, self.depth):
			self.nega_alpha(self.turn, d, -INF, INF)
		ev = self.nega_alpha(self.turn, self.depth, -INF, INF)

		pv = []
		t = self.turn
		for d in range(self.depth):
			try:
				board = max((self.table[b], b) for b in board.next_boards(t))[1]
				pv.append(board)
				if board.status != 0:
					break
			except ValueError:
				break
			t *= -1

		return ev, pv

	def nega_alpha(self, turn, depth, alpha, beta):

		if self.board.status != 0: # end state
			self.table[self.board] = (100, depth*10)
			return -depth*10

		if depth <= 0:
			s = np.asscalar(self.model.predict(self.board._board.reshape((1,42)))*turn)
			self.table[self.board] = (depth, -s)
			return s


		child_info = [(self.table[h], h, x) for h,x in self.board.next_board_hashes(turn)]

		if not child_info:
			self.table[self.board] = (0, 0)
			return 0

		child_info.sort(reverse=True)

		original_hash = self.board.hash

		best = None
		for _, h, x in child_info:

			self.board.Dmake_move(x, turn, h)
			score = -self.nega_alpha(-turn, depth-1,-beta,-alpha)
			self.board.revert(x, original_hash)

			if alpha < score:
				alpha = score
				best = h
				if alpha >= beta:
					break

		if best:
			self.table[best] += 1

		self.table[self.board] = (depth, -alpha)
		return alpha