from copy import deepcopy
import numpy as np
from itertools import count
from collections import defaultdict


END_INT = 50000
CHAIN_SCORE = [0, 0, 100, 300, 100000, 100000, 100000, 100000]

H = 6
W = 7


TABLE = defaultdict(int)
TABLE_MAX_SIZE = 100000000

class Board:
	def __init__(self, starting_board = False):
		if starting_board:
			self._board = np.zeros((W,H), dtype='int8')
			self._next_empty_y = np.zeros(W, dtype='int8')
			self.last_move = None
			self.score = 0
			#self.hash = int('0000001'*7,2)

	def next_boards(self, color):
		for x in range(W):
			if self._next_empty_y[x] < H:
				yield self.make_move(color, x)

	dlist = [(1,1),(1,0),(0,1),(1,-1)]

	def make_move(self, color, x):
		y = self._next_empty_y[x]

		nboard = Board()
		nboard._board = np.copy(self._board)
		nboard._next_empty_y = np.copy(self._next_empty_y)
		nboard.last_move = x
		"""
		if color == 1:
			nboard.hash = self.hash ^ (2 << (x*7+y))
		else:
			nboard.hash = self.hash ^ (3 << (x*7+y))
		"""
		nboard[x,y] = color
		nboard._next_empty_y[x] += 1


		dscore = 3 - abs(x-3)
		#dscore = 0
		for dx,dy in Board.dlist:
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


	def __getitem__(self, key):
		return self._board[key]

	def __setitem__(self, key, item):
		self._board[key] = item

	def __repr__(self):
		s = ' '.join(str(i) for i in range(W))+' \n'
		r = {-1:'○', 0: '  ', 1: '●'}
		l = {-1:'□', 1: '■'}

		ly = self._next_empty_y[self.last_move]-1

		for y in reversed(range(H)):
			for x in range(W):
				if x == self.last_move and y == ly:
					s+=l[self[x,y]]
				else:
					s+=r[self[x,y]]
			s+='\n'

		s+= 'last move: '+str(self.last_move) +'\n'
		return s

	def __lt__(self, other):
		return False


def table_value(depth, score):
	return (depth << 24) + score



def nega_alpha(board, turn, depth, alpha, beta):

	if depth <= 0:
		return board.score*turn, []
	if abs(board.score) > END_INT:
		return -END_INT - depth, []

	nexts = list(board.next_boards(turn))

	if not nexts:
		return 0, []

	#child_info = [(TABLE[b.hash],b) for b in nexts].sort(reverse=True)
	child_info = [(b.score,b) for b in nexts]
	child_info.sort(reverse= True)
	best_pv = []
	for s, nboard in child_info:
		score, pv = nega_alpha(nboard, -turn, depth-1,-beta,-alpha)
		score = -score

		if alpha < score:
			#TABLE[nboard.hash] = table_value(depth, score)
			best_pv = pv + [nboard]
			alpha = score
			if alpha >= beta:
				return alpha, best_pv

	return alpha, best_pv

def iddfs(board, turn, Max_depth):

	for d in range(1, Max_depth+1):
		pass


board = Board(starting_board=True)

print('Bot goes: first(F) or second(S)? ', end='')
turn = (input() == 'F')*2-1
print('Bot depth: ', end='')
DEPTH = int(input())
print('Bot color is always ●')


import time
"""
for d in range(DEPTH):
	print(d)
	nega_alpha(board, turn, d, -END_INT*3, END_INT*3)
"""
while True:
	score = board.score
	if abs(score) > END_INT:
		if score > 0:
			print('Bot won')
		else:
			print('You won')
		break

	if all(board[x,5] != 0 for x in range(7)):
		print('Draw')
		break

	if turn == 1:
		start = time.process_time()
		ev, pv = nega_alpha(board, turn, DEPTH, -END_INT*3, END_INT*3)
		stop = time.process_time()
		pv = pv[::-1]

		board = pv[0]
		print(board)

		print('Evaluation:',ev)
		print('PV: '+', '.join(map(str, (b.last_move for b in pv))))
		print('Time: '+str(stop-start)+'s')

	else:
		while True:
			print('Move? ', end='')
			try:
				move = int(input())
			except ValueError:
				print('Specify the move in integer (0 ... 6)')
				continue
			if board[move,H-1] != 0:
				print('That column is full')
				continue
			break

		board = board.make_move(turn, move)
		print(board)

	print('--------------')

	turn *= -1