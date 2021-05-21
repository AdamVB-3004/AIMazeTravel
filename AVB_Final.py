import sys
import csv
import random 
import numpy
from pandas import DataFrame

#Written by AdamVB
#Tested on Windows 10 with python 3.9.1

#TODO
#Check if the best path is still valid instead of recalculating it

#The player Object, contains all relavent info for the players
class Player:
	def __init__(self, location, opponents, target, home, name, player=False):
		self.name = name
		self.location = location 	#Player's current location
		self.opponents = opponents	#Name's of the opponents
		self.home = home			#Homebase cords
		self.target = target		#Enemy flag locations
		self.player = player		#Is the player human?
		self.ontopof = None 		#What the player is standing on
		self.timeout = False 		#Flag for if they've been attacked, lose a turn
		self.gameover = False		#Flag for the end of the game
		self.steps = 0				#Number of steps taken so far
		#self.best_path = []			#Current best path from aStar
		
	#Player functions
	#Set what is currently under the player
	def standing_on(self, thing):
		self.ontopof = thing
	
	#handle getting attacked
	def attack(self):
		self.timeout = True
	
	#reset timeout
	def wakeUp(self):
		self.timeout = False
		
	def winner(self):
		self.gameover = True
	
	def moved(self, cost=0):
		self.steps += 1 + cost
	
	def isGoal(self, location):
		if location in self.target:
			return True
		else:
			return False
	
#build a maze with desired MxN dimentions
#input: height -> height of maze from user input
#		width -> width of maze from user input
def buildMaze(height, width, player_count):
	maze_array = []
	tempInner= []
	goals = []
	player_names = []
	print("Creating randomized maze...")
	
	while 1:
		#create the randomized path costs
		for m in range(0, height):
			for n in range(0, width):
				if m == 0 and n == 0:
					#place Alice
					tempInner.append('A')
					player_names.append('A')
					goals.append((m,n))
					continue
				elif player_count > 2 and m == 0 and n == width - 1:
					#Place bob
					tempInner.append('B')
					player_names.append('B')
					goals.append((m, n))
					continue
				elif player_count > 3 and m == height-1 and n == 0:
					#Place Charlie
					tempInner.append('C')
					player_names.append('C')
					goals.append((m, n))
					continue
				elif m == height-1 and n == width-1:
					#place Dana
					tempInner.append('D')
					player_names.append('D')
					goals.append((m,n))
					continue 
				#
				r = random.randint(1, 10)
				if r == 10:
					tempInner.append('X')
				else:
					tempInner.append(r)
			maze_array.append(tempInner)
			tempInner = []
			
		#check for a path?
		#TEMP just ask user
		print(DataFrame(data=maze_array, index=['' for x in range(0, len(maze_array[0]))],
						columns=['' for x in range(0, len(maze_array))]))
		print()
		check = input("Is the maze solveable? (y/n): ")
		if check == 'y' or check == 'Y':
			break
		else:
			#reset
			maze_array = []
			tempInner= []
			goals = []
			player_names = []

	print("Maze: Done.\n")
	return maze_array, goals, player_names

#find next actions of a given state, for min_max function
def get_actions(position, maze, targets):
	action_list = []
	values = []
	
	if position[0] - 1 >= 0 and \
		maze[position[0]-1][position[1]] != 'X':
		#Up is valid
		for x in targets:#Check against each target
			values.append(abs(position[0]-1 - x[0]) + abs(position[1] - x[1]))
		value = min(values)
		action_list.append(((position[0]-1, position[1]), value))
	
	if position[1] + 1 < len(maze[position[0]]) and \
		maze[position[0]][position[1]+1] != 'X':
		#Right is valid
		for x in targets:#Check against each target
			values.append(abs(position[0] - x[0]) + abs(position[1]+1 - x[1]))
		value = min(values)
		action_list.append(((position[0], position[1]+1), value))
	
	if position[0] + 1 < len(maze)  and \
		maze[position[0]+1][position[1]] != 'X':
		#Down is valid
		for x in targets:#Check against each target, picking the lowest
			values.append(abs(position[0]+1 - x[0]) + abs(position[1] - x[1]))
		value = min(values)
		action_list.append(((position[0]+1, position[1]),value))
	
	if position[1] - 1 >= 0  and \
		maze[position[0]][position[1]-1] != 'X':
		#Left is valid
		for x in targets:#Check against each target
			values.append(abs(position[0] - x[0]) + abs(position[1]-1 - x[1]))
		value = min(values)
		action_list.append(((position[0], position[1]-1), value))
	
	#Sort action list by values then remove the values
	sorted_action_list = [i[0] for i in sorted(action_list, key=lambda x: x[1])]
	return sorted_action_list
	
#min-max with alpha beta pruning
#AI wants to block the most valuable path of oppenent
#algrothim taken from notes and adjusted to the requirements of this program
#But still moving to goal
#Players -> the list of Player objects in the game
#Alpha, Beta -> the alpha and beta values for the min-max search
#Maze -> the maze
#Steps -> the "score" for the search
#max_depth -> The deepest the search will consider
#playerCnt -> the number of players
#mainPlayer -> the player being considered
#is_max -> is the current iteration a max node
def min_max(players, alpha, beta, maze, steps,\
			max_depth, playerCnt, turnNo, mainPlayer, is_max=True):
	values = []
	#Calculate the next turn
	if turnNo == playerCnt - 1:
		nextTurn = 0
	else:
		nextTurn = turnNo + 1
	
	if max_depth <= 0: #Cut off endless loops
		return players[turnNo].location, steps
	
	if is_max and players[turnNo].isGoal(players[turnNo].location):
		return players[turnNo].location, steps + 100
	elif not is_max and players[turnNo].isGoal(players[turnNo].location):
		return players[turnNo].location, steps 
	
	if not is_max: #Only count current player turns
		try:
			steps += 1 + int(maze[players[turnNo].location[0]][players[turnNo].location[1]])
		except ValueError:
			steps += 1
	
	#If player is stunned wake them up and pass the turn
	if players[turnNo].timeout:
		players[turnNo].wakeUp()
		#Check if the next player is in the main
		if players[nextTurn].name == mainPlayer:#min player
			v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
						playerCnt, nextTurn, mainPlayer, is_max=False)
			if v[1] >= beta:
					return v
			values.append((players[turnNo].location, v[1]))
		else: #max player
			v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
						playerCnt, nextTurn, mainPlayer)
			if v[1] <= alpha:
				return v
			values.append((players[turnNo].location, v[1]))
	else:
		#Otherwise check each possible action
		for a in get_actions(players[turnNo].location, maze, players[turnNo].target):
			players[turnNo].location = a
			if is_max:
				#Enemy steped on player, skip turn
				if a in [x.location for x in (players[:turnNo] + players[(turnNo+1):])]:
					for x in players:
						if x.name == mainPlayer and x.location == a:
							steps += 1
							x.attack()
					if players[nextTurn].name == mainPlayer:#min player
						v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
									playerCnt, nextTurn, mainPlayer, is_max=False)
						if v[1] >= beta:
							return v
					else: #max player
						v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
									playerCnt, nextTurn, mainPlayer)
						if v[1] <= alpha:
							return v
				elif a in players[turnNo].target: #Enemy won, skip players turn
					v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
								playerCnt, turnNo, mainPlayer)
					if v[1] <= alpha:
						return v
				else: #Normal turn
					if players[nextTurn].name == mainPlayer:#min player
						v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
									playerCnt, nextTurn, mainPlayer, is_max=False)
						if v[1] >= beta:
							return v
					else: #max player
						v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
									playerCnt, nextTurn, mainPlayer)
						if v[1] <= alpha:
							return v
					
				values.append((a, v[1]))
				alpha = max(alpha, v[1])
			else:#Is the main player
				 #Stepped on other player, skip their turn
				if a in [x.location for x in (players[:turnNo] + players[(turnNo+1):])]:
					v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
								playerCnt, nextTurn, mainPlayer)
					if v[1] <= alpha:
						return v
				elif a in players[turnNo].target: #Player has won, ignore next players turn
					v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
								playerCnt, turnNo, mainPlayer, is_max=False)
					if v[1] >= beta:
						return v
				else: #Normal turn
					v = min_max(players, alpha, beta, maze, steps, max_depth-1,\
								playerCnt, nextTurn, mainPlayer)
					if v[1] <= alpha:
						return v
				values.append((a, v[1]))
				
				if v[1] <= alpha:
					return v 
				beta = min(beta, v[1])
	
	if is_max:
		action, value = max(values, key=lambda x:x[1])
	else:
		action, value = min(values, key=lambda x:x[1])

	return action, value

#Change the maze to display the move
def make_move(player, players, maze, next):
	prev_pos = player.location
	temp = maze[next[0]][next[1]] #Holding for next space
	
	#Move player to next space
	if next in player.target:
		#End the game
		maze[next[0]][next[1]] = maze[prev_pos[0]][prev_pos[1]]
		maze[prev_pos[0]][prev_pos[1]] = player.ontopof
		player.winner()
	elif temp in player.opponents:
		#Attack opponent then move
		for victim in players:
			if victim.name == temp:
				victim.attack()
				player.moved(victim.ontopof)
		maze[next[0]][next[1]] = maze[prev_pos[0]][prev_pos[1]]
		maze[prev_pos[0]][prev_pos[1]] = player.ontopof
	else:
		maze[next[0]][next[1]] = maze[prev_pos[0]][prev_pos[1]]
		maze[prev_pos[0]][prev_pos[1]] = player.ontopof
		try:
			player.moved(int(temp))
		except ValueError:
			player.moved()
	
	#Set what the player is standing on
	player.standing_on(temp)
	player.location = next
	
	return maze

#Handle human player inputs	
def playerAction(player, maze):
	print(DataFrame(data=maze, index=['' for x in range(0, len(maze[0]))],
						columns=['' for x in range(0, len(maze))]))
	print("\nIt's your turn!\nValid actions: (u)p, (d)own, (l)eft, (r)ight.")
	currPos = player.location 
	
	while 1:
		u_in = input("> ")
		if u_in.lower() == 'u': #Handle UP input
			if currPos[0] - 1 >= 0 and \
				maze[currPos[0]-1][currPos[1]] != 'X':
				move = (currPos[0]-1, currPos[1])
				break
			else:
				print("You can't go that way!")
				continue
		elif u_in.lower() == 'd':#Handle DOWN input
			if currPos[0] + 1 < len(maze) and \
				maze[currPos[0]+1][currPos[1]] != 'X':
				move = (currPos[0]+1, currPos[1])
				break
			else:
				print("You can't go that way!")
				continue
		elif u_in.lower() == 'l':#Handle LEFT input
			if currPos[1]-1 >= 0 and \
				maze[currPos[0]][currPos[1]-1] != 'X':
				move = (currPos[0], currPos[1]-1)
				break
			else:
				print("You can't go that way!")
				continue
		elif u_in.lower() == 'r':#Handle RIGHT input
			if currPos[1]+1 < len(maze[0]) and \
				maze[currPos[0]][currPos[1]+1] != 'X':
				move = (currPos[0], currPos[1]+1)
				break
			else:
				print("You can't go that way!")
				continue
		else: #Invalid input error
			print("Please enter u, d, l, or r.")
			continue
	return move

#Handle a turn
def turnManager(players, maze, h):
	#Start with player 1
	turn = 0
	next = 1
	player_no = len(players)
	gameRunning = True
	
	while gameRunning:
		#Do turn things
		#Check if stunned
		if players[turn].timeout:
			players[turn].wakeUp()
			#Set next player
			if turn == player_no - 1:
				turn = 0
				next = 1
			else:
				turn += 1
				if next + 1 >= player_no:
					next = 0
				else:
					next += 1
			continue#Skip turn
		
		#If it's a human player
		if players[turn].player:
			#Get player action
			next_move = playerAction(players[turn], maze)
		else:#AI otherwise
			#Temp store values to reset after
			#Sloppy but easy
			prevLocations = []
			for x in players:
				prevLocations.append((x.location, x.timeout))
			
			#Use minmax to find next best move
			next_move = min_max(players, -numpy.inf, numpy.inf,
								maze, 0,
								(len(maze) * len(maze[0])),
								player_no, turn, players[turn].name, is_max=False)[0]
			
			#restore previous locations/timeouts
			for i, x in enumerate(players):
				x.location = prevLocations[i][0]
				x.timeout = prevLocations[i][1]
		
		#Make move
		maze = make_move(players[turn], players, maze, next_move)
		print("Player: " + players[turn].name + " -> " + str(next_move))
		print(DataFrame(data=maze, index=['' for x in range(0, len(maze[0]))],
						columns=['' for x in range(0, len(maze))]))
		print()
		
		#Wrap up the game
		if players[turn].gameover:
			print("The Winner is: ", players[turn].name)
			print("Score: ", players[turn].steps)
			break
		
		#Set next player
		if turn == player_no - 1:
				turn = 0
				next = 1
		else:
			turn += 1
			if next + 1 >= player_no:
				next = 0
			else:
				next += 1
	return
	
def pathfinding():
	#Set the players 
	#Ask if a human player will exist
	#default 2 AI
	while 1:
		n = input("How many players (2-4)?\n> ")
		try:
			if int(n) >= 2 and int(n) <= 4:
				player_count = int(n)
				break
			else:
				print("Please enter a 2, 3, or 4.")
		except ValueError:
			print("Please enter a 2, 3, or 4.")

	#Get user input for the maze
	while 1:
		input_m = input("What maze height? > ")
		try:
			m = int(input_m)
			if m <= 0:
				print("Invalid input")
				continue
			break
		except ValueError:
			print("Invalid input [1-100].")
	while 1:
		input_n = input("What maze width? > ")
		try:
			n = int(input_n)
			if n <= 0:
				print("Invalid input [1-100].")
				continue
			break
		except ValueError:
			print("Invalid input")
	
	#Generate a randomized array with size MxN
	maze_array, goals, player_names = buildMaze(m, n, player_count)
	players = []
	
	#DEBUG MAZE
	#maze_array = [['A', 7, 3, 3,9], [1, 4, 5, 3,8], [7, 3, 5, 7,5], [1, 7, 2, 1,8], ['X', 2, 3, 7, 'D']]
	#goals = [(0,0), (4,4)]
	#player_names = ['A', 'D']
	while 1:
		input_n = input("Will there be a human player?\n(y/n): ")
		if input_n == 'y' or input_n == 'Y':
			#one human player
			print("**Not tested properly, expect bugs.**")
			
			while 1:
				u_in = input("Player 1, 2, 3, or 4?\n> ")
				if u_in == '1':
					player_flag = 0
					break
				elif u_in == '2':
					player_flag = 1
					break
				elif u_in == '3' and player_count > 2:
					player_flag = 2
					break
				elif u_in == '4' and player_count > 3:
					player_flag = 3
					break
				else:
					print("Please enter 1, 2, 3, or 4.")
					
			players = []
			for i in range(0, player_count):
				opponents = player_names[:i] + player_names[(i+1):]
				targets = goals[:i] + goals[(i+1):]
				
				if player_flag == i:
					players.append(Player(goals[i], opponents, targets, goals[i], player_names[i], player=True))
				else:
					players.append(Player(goals[i], opponents, targets, goals[i], player_names[i]))
				players[i].standing_on(player_names[i] + 'F')
			break
		elif input_n == 'n' or input_n == 'N':
			#initilize players
			for i in range(0, player_count):
				opponents = player_names[:i] + player_names[(i+1):]
				targets = goals[:i] + goals[(i+1):]
				
				#Set the players current location(homebase at start, 
				#		oppenent names, target list, and player name
				players.append(Player(goals[i], opponents, targets, goals[i], player_names[i]))
				players[i].standing_on(player_names[i] + 'F')
			break
	

	#set the heuristics using a lambda function
	#Need a new heuristic based on traps/buffs
	h = lambda a, b: (abs(a[0] - b[0]) + abs(a[1] - b[1]))
	
	#Start the simulation
	turnManager(players, maze_array, h)
	
	return

print("Running pathfinding...")
pathfinding()