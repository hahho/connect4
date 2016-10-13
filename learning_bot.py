from basics import *
import numpy as np
import utils
import keras.models


INF = 6000

class LBoard(Board):
	def __init__(self, starting_board = False ):
		super().__init__(starting_board)
		if starting_board:
			self._board = np.zeros((W,H), dtype='int8')
			self._next_empty_y = np.zeros(W, dtype='int8')
			self.hash = utils.START_HASH
			self.status = IN_PROGRESS

	
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
			self.status = IN_PROGRESS

		if y == H-1 and all(self[x,H-1] != 0 for x in range(W)):
			self.status = DRAW

	def revert(self, x, h):
		y = self._next_empty_y[x]-1
		self._next_empty_y[x] = y

		self._board[x,y] = 0
		self.hash = h
		self.status = IN_PROGRESS


	def __getitem__(self, key):
		return int(self._board[key])

	def __setitem__(self, key, item):
		self._board[key] = item

	def __lt__(self, other):
		return False


class LearningBot(Bot):
	def __init__(self, turn, model='model.kmodel',
		depth=6, time=None, debug=False, quiet=False,
		shared_hashtable = None):

		super().__init__(turn)
		self.depth = depth
		self.time = time
		self.debug = debug
		self.board = None
		self.quiet = quiet
		if type(model) == str:
			self.model = keras.models.load_model(model)
		else:
			self.model = model

		if shared_hashtable is not None:
			self.table = shared_hashtable
		else:
			self.table = utils.HashTable()

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
			self.nega_alpha(self.turn, d, -INF, INF)
		ev = self.nega_alpha(self.turn, self.depth, -INF, INF)

		pv = []
		t = self.turn
		for d in range(self.depth):
			try:
				board = max((self.table[b], b) for b in board.next_boards(t))[1]
				pv.append(board)
				if board.status != IN_PROGRESS:
					break
			except ValueError:
				break
			t *= -1
		return ev, pv

	def generate_move_for_learning(self, board):
		searched_depth = self.table[board][0]

		self.board = board
		for d in range(searched_depth+1, self.depth):
			self.nega_alpha(self.turn, d, -INF, INF)
		ev = self.nega_alpha(self.turn, self.depth, -INF, INF)


		best = max((self.table[h],h,x) for h,x in self.board.next_board_hashes(self.turn))

		board.Dmake_move(best[2],self.turn,best[1])
		return ev, board

	def nega_alpha(self, turn, depth, alpha, beta):

		if abs(self.board.status) == 1: # end state
			self.table[self.board] = (100, depth*10)
			return -depth*10

		if self.board.status == DRAW:
			self.table[self.board] = (0, 0)
			return 0

		if depth <= 0:
			s = np.asscalar(self.model.predict(self.board._board.reshape((1,42)))*turn)
			self.table[self.board] = (depth, -s)
			return s


		child_info = [(self.table[h], h, x) for h,x in self.board.next_board_hashes(turn)]

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
			self.table[best] = (self.table[best][0], self.table[best][1]+1e-16)

		self.table[self.board] = (depth, -alpha)
		return alpha