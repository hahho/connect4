from basics import *
from bot1 import Aegis, NPBoard
from learning_bot import LearningBot, LBoard
import keras.models
#setup

def ask_bot_options():
	print('Options for this bot like \"depth=1,time=30,debug=true\": ', end='')
	s = input()
	args = {t[0].strip():t[1].strip() for t in map(lambda v: v.split('='), s.split(','))}
	for k,v in args.items():
		if v[0].lower() == 't':
			args[k] = True
		elif v[0].lower() == 'f':
			args[k] = False
		else:
			try:
				args[k] = int(v)
			except ValueError:
				pass
	print(args)
	return args



current_Bot = Aegis
current_Board = NPBoard
#model = keras.models.load_model('model.kmodel')
assert issubclass(current_Bot, Bot), 'current_BotがBot型になってない'
assert issubclass(current_Board, Board), 'current_BoardがBoard型になってない'

print('First player [(H)uman or (B)ot]: ', end='')
if input().lower() == 'h':
	first_player = Human(1)
else:
	first_args = ask_bot_options()
	first_player = current_Bot(1, **first_args)
	#first_player = current_Bot(1, model=model, **first_args)

print('Second player [(H)uman or (B)ot]: ', end='')
if input().lower() == 'h':
	second_player = Human(-1)
else:
	second_args = ask_bot_options()
	second_player = current_Bot(-1, **second_args)
	#second_player = current_Bot(-1, model=model, **second_args)

if isinstance(first_player, Bot) and isinstance(second_player, Bot):
	print('# of games: ', end='')
	N = int(input())
else:
	N = 1


#actual game

board = current_Board(starting_board=True)
history = [board]

def turn_handling(player):
	global board,history

	if isinstance(player, Human):
		print('Move(0...8) or Back(b)?: ', end='')
		s = input()
		while True:
			if s.lower() == 'b':
				history = history[:-2]
				board = history[-1]
				print(board)
				print('Move(0...8) or Back(b)?: ', end='')
				s = input()
			else:
				try:
					move = int(s)
					break
				except ValueError:
					continue
		board = board.make_move(move, player.turn)
		history = history + [board]
		print(board)

	elif isinstance(player, Bot):
		ev, pv = player.generate_move(board)
		board = pv[0]
		history = history + [board]
		print(board)
		print('Evaluation :',ev)
		print('PV :', ', '.join(map(lambda b: str(b.last_move), pv)))

	else:
		print('wtf are you')

first_wins = 0
second_wins = 0
draws = 0

import time

for i in range(1, N+1):

	if N > 1:
		first_player = current_Bot(1, **first_args)
		second_player = current_Bot(1, **second_args)
		board = current_Board(starting_board=True)
		history = [board]

	turn = True

	while board.status is IN_PROGRESS:
		start = time.time()
		turn_handling(first_player if turn else second_player)
		stop = time.time()
		print('Time =',stop-start, 's')
		print('--------------')
		turn = not turn

	if board.status is FIRST_WIN:
		print(first_player.name,'(First Player) wins')
		first_wins += 1
	elif board.status is SECOND_WIN:
		print(second_player.name,'(Second Player) wins')
		second_wins += 1
	elif board.status is DRAW:
		print('Draw')
		draws += 1
	else:
		print('something is wrong:',status)