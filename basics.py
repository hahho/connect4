
W = 7
H = 6

class Player:
	def __init__(self, name, turn):
		self.name = name
		self.turn = turn

class Human(Player):
	def __init__(self, turn):
		super().__init__('Human', turn)

class Bot(Player):
	def __init__(self, turn):
		super().__init__('Bot', turn)

	def generate_move(self, board):
		"""
		This should return evaluation value, and PV (its reading as a list of boards)
		"""
		pass

FIRST_WIN = 1		# keep these constants
SECOND_WIN = -1		#
IN_PROGRESS = 0
DRAW = 2

class Board:
	def __init__(self, starting_board = False):
			if starting_board:
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
