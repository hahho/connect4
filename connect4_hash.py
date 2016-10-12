from copy import deepcopy
import numpy as np
from itertools import count
from collections import defaultdict


END_INT = 50000
CHAIN_SCORE = [0, 0, 100, 300, 100000, 100000, 100000, 100000]

H = 6
W = 7


TABLE = defaultdict(int)

class Board:
	def __init__(self, starting_board = False):
		if starting_board:
			self._board = np.zeros((W,H), dtype='int8')
			self._next_empty_y = np.zeros(W, dtype='int8')
			self.last_move = None
			self.score = 0
			self.hash = int('0000001'*7,2) << 6

	def next_boards(self, color):
		for x in range(W):
			if self._next_empty_y[x] < H:
				yield self.make_move(color, x)

	dlist = [(1,1),(1,0),(0,1),(1,-1)]

	def make_move(self, color, x):
		y = int(self._next_empty_y[x])

		nboard = Board()
		nboard._board = np.copy(self._board)
		nboard._next_empty_y = np.copy(self._next_empty_y)
		nboard.last_move = x
		
		if color == 1:
			nboard.hash = (self.hash ^ (2 << (x*7+y)+6)) + 1
		else:
			nboard.hash = (self.hash ^ (3 << (x*7+y)+6)) + 1
		
		nboard[x,y] = color
		nboard._next_empty_y[x] += 1


		dscore = 3 - abs(x-3)
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
		r = {-1:'○', 0: '・', 1: '●'}
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
	return (depth << 24) | (score+ (1 << 23))

def Tval_to_DS(table_val):
	return table_val >> 24, (table_val & 0xFFFFFF) - (1 << 23)



def nega_alpha(board, turn, depth, alpha, beta):

	if depth <= 0:
		return board.score*turn, []
	if abs(board.score) > END_INT:
		return -END_INT - depth, []

	nexts = list(board.next_boards(turn))

	if not nexts:
		return 0, []

	child_info = [(TABLE[b.hash],b) for b in nexts]
	child_info.sort(reverse= True)
	best_pv = []
	for s, nboard in child_info:
		score, pv = nega_alpha(nboard, -turn, depth-1,-beta,-alpha)
		score = -score
		TABLE[nboard.hash] = max(TABLE[nboard.hash], table_value(depth, score))

		if alpha < score:
			best_pv = pv + [nboard]
			alpha = score
			if alpha >= beta:
				return alpha, best_pv

	return alpha, best_pv

def iddfs(board, turn, Max_depth):

	for d in range(1, Max_depth+1):
		pass

def shrink_table(moves):
	global TABLE
	mask = int('11111',2)
	TABLE = defaultdict(int, ({(h,v) for h,v in TABLE.items() if (h & mask) >= moves}))

board = Board(starting_board=True)

print('Bot goes: first(F) or second(S)? ', end='')
turn = (input() == 'F')*2-1
print('Bot depth: ', end='')
DEPTH = int(input())
print('Bot color is always ●')


import time

for d in range(DEPTH):
	print(d)
	nega_alpha(board, turn, d, -END_INT*3, END_INT*3)


history = [board]
while True:
	score = board.score
	"""
	s = bin(board.hash)[::-1]
	ss = ' '.join([s[:6],s[6:13],s[13:20],s[20:27],s[27:34],s[34:41],s[41:48],s[48:]])
	print(ss[::-1])
	"""
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

		depth = DEPTH-1 if len(history) < 10 else DEPTH
		print('current table size =',len(TABLE))
		shrink_table(len(history)-1)
		print('Table shrink, now the size =', len(TABLE))
		start = time.process_time()
		ev, pv = nega_alpha(board, turn, depth, -END_INT*3, END_INT*3)
		stop = time.process_time()
		pv = pv[::-1]


		board = pv[0]
		history += [board]
		print(board)

		print('Evaluation:',ev)
		print('PV: '+', '.join(map(str, (b.last_move for b in pv))))
		print('Time: '+str(stop-start)+'s')

	else:
		while True:
			print('Move? ', end='')
			try:
				s = input()
				if s == 'back':
					history = history[:-2]
					board = history[-1]
					print(board)
					continue
				else:
					move = int(s)
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