
W = 7
H = 6

class Player:
	def __init__(self, name):
		self.name = name

class Human(Player):
	def __init__(self):
		super().__init__('Human')

class Bot(Player):
	def __init__(self):
		super().__init__('Bot')

	def generate_move(self, board, turn):
		"""
		This should return evaluation value, and PV (its reading as a list of boards)
		"""
		pass

FIRST_WIN = 1		# keep these constants
SECOND_WIN = -1		#
IN_PROGRESS = -2
DRAW = 0

class Board:
	def __init__(self, board=None, initialize = False):
		if initialize:
			self.last_move = None

	def make_move(self, x, color):
		pass


	def __getitem__(self, key):
		pass

	def __repr__(self):
		s = ' '.join(str(i) for i in range(W))+' \n'
		r = {-1:'○ ', 0: '・', 1: '● '}
		l = {-1:'□ ', 1: '■ '}

		ly = H-1
		while self[self.last_move,ly] == 0:
			ly -= 1

		for y in reversed(range(H)):
			for x in range(W):
				if x == self.last_move and y == ly:
					s+=l[self[x,y]]
				else:
					s+=r[self[x,y]]
			s+='\n'

		s+= 'last move: '+str(self.last_move) +'\n'
		return s
