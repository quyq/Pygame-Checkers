"""
checkers.py

A simple checkers engine written in Python with the pygame 1.9.1 libraries.

Here are the rules I am using: http://boardgames.about.com/cs/checkersdraughts/ht/play_checkers.htm

I adapted some code from checkers.py found at 
http://itgirl.dreamhosters.com/itgirlgames/games/Program%20Leaders/ClareR/Checkers/checkers.py starting on line 159 of my program.

This is the final version of my checkers project for Programming Workshop at Marlboro College. The entire thing has been rafactored and made almost completely object oriented.

Funcitonalities include:
- Having the pieces and board drawn to the screen
- The ability to move pieces by clicking on the piece you want to move, then clicking on the square you would
  like to move to. You can change you mind about the piece you would like to move, just click on a new piece of yours.
- Knowledge of what moves are legal. When moving pieces, you'll be limited to legal moves.
- Capturing
- DOUBLE capturing etc.
- Legal move and captive piece highlighting
- Turn changes
- Automatic kinging and the ability for them to move backwords
- Automatic check for and end game. 
- A silky smoooth 60 FPS!

Everest Witman - May 2014 - Marlboro College - Programming Workshop 
"""

import pygame
from pygame.locals import *
import re

pygame.font.init()

##COLORS##
#             R    G    B 
WHITE    = (255, 255, 255)
BLUE     = (  0,   0, 255)
RED      = (255,   0,   0)
BLACK    = (  0,   0,   0)
GOLD     = (255, 215,   0)
HIGH     = (160, 190, 255)

##DIRECTIONS##
NORTHWEST = "northwest"
NORTHEAST = "northeast"
SOUTHWEST = "southwest"
SOUTHEAST = "southeast"

#NET_EVENT = pygame.event.custom_type()
NET_EVENT = pygame.USEREVENT + 1

class Game:
	"""
	The main game control.
	"""

	def __init__(self, session=None):
		self.graphics = Graphics()
		self.board = Board()
		
		self.turn = BLUE
		self.selected_piece = None # a board location. 
		self.hop = False
		self.selected_legal_moves = []
		self.session = session

	def setup(self):
		"""Draws the window and board at the beginning of the game"""
		self.graphics.setup_window()

	def event_loop(self):
		"""
		The event loop. This is where events are triggered 
		(like a mouse click) and then effect the game state.
		"""
		self.mouse_pos = self.graphics.board_coords(pygame.mouse.get_pos()) # what square is the mouse in?
		if self.selected_piece != None:
			self.selected_legal_moves = self.board.legal_moves(self.selected_piece, self.hop)

		for event in pygame.event.get():

			if event.type == QUIT:
				self.terminate_game()

			if self.session!=None:
				if self.session.conn==None: continue    # skip if no connection
				# server is BLUE, client is RED
				if (self.session.role=='server' and self.turn==RED) or (self.session.role=='client' and self.turn==BLUE):
					if event.type == NET_EVENT:	# process the data
						#print("Received: ", event.data)
						self.mouse_pos = (event.data[0], event.data[1])
						event = pygame.event.Event(MOUSEBUTTONDOWN)	# mimic as MOUSEBUTTONDOWN
					else: continue	# ignore other events as it is not my turn

			if event.type == MOUSEBUTTONDOWN:
				if self.session!=None and self.session.conn!=None:
					self.session.conn.send(bytes(self.mouse_pos)) # sync mouse event to remote side
				if self.hop == False:
					if self.board.location(self.mouse_pos).occupant != None and self.board.location(self.mouse_pos).occupant.color == self.turn:
						self.selected_piece = self.mouse_pos
					elif self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece):
						self.board.move_piece(self.selected_piece, self.mouse_pos)
					
						if self.mouse_pos not in self.board.adjacent(self.selected_piece):
							self.board.remove_piece(((self.selected_piece[0] + self.mouse_pos[0]) >> 1, (self.selected_piece[1] + self.mouse_pos[1]) >> 1))
							self.hop = True
							self.selected_piece = self.mouse_pos
						else:
							self.end_turn()

				if self.hop == True:					
					if self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece, self.hop):
						self.board.move_piece(self.selected_piece, self.mouse_pos)
						self.board.remove_piece(((self.selected_piece[0] + self.mouse_pos[0]) >> 1, (self.selected_piece[1] + self.mouse_pos[1]) >> 1))

					if self.board.legal_moves(self.mouse_pos, self.hop) == []:
						self.end_turn()
					else:
						self.selected_piece = self.mouse_pos


	def update(self):
		"""Calls on the graphics class to update the game display."""
		self.graphics.update_display(self.board, self.selected_legal_moves, self.selected_piece)

	def terminate_game(self):
		"""Quits the program and ends the game."""
		pygame.quit()
		sys.exit

	def main(self):
		""""This executes the game and controls its flow."""
		self.setup()

		while True: # main game loop
			self.event_loop()
			self.update()

	def end_turn(self):
		"""
		End the turn. Switches the current player. 
		end_turn() also checks for and game and resets a lot of class attributes.
		"""
		if self.turn == BLUE:
			self.turn = RED
		else:
			self.turn = BLUE
		self.selected_piece = None
		self.selected_legal_moves = []
		self.hop = False

		if self.check_for_endgame():
			if self.turn == BLUE:
				self.graphics.draw_message("RED WINS!")
			else:
				self.graphics.draw_message("BLUE WINS!")

	def check_for_endgame(self):
		"""
		Checks to see if a player has run out of moves or pieces. If so, then return True. Else return False.
		"""
		for x in range(8):
			for y in range(8):
				if self.board.location((x,y)).color == BLACK and self.board.location((x,y)).occupant != None and self.board.location((x,y)).occupant.color == self.turn:
					if self.board.legal_moves((x,y)) != []:
						return False

		return True

class Graphics:
	def __init__(self):
		self.caption = "Checkers"

		self.fps = 60
		self.clock = pygame.time.Clock()

		self.window_size = 600
		self.screen = pygame.display.set_mode((self.window_size, self.window_size))
		self.background = pygame.image.load('resources/board.png')

		self.square_size = self.window_size >> 3
		self.piece_size = self.square_size >> 1

		self.message = False

	def setup_window(self):
		"""
		This initializes the window and sets the caption at the top.
		"""
		pygame.init()
		pygame.display.set_caption(self.caption)

	def update_display(self, board, legal_moves, selected_piece):
		"""
		This updates the current display.
		"""
		self.screen.blit(self.background, (0,0))
		
		self.highlight_squares(legal_moves, selected_piece)
		self.draw_board_pieces(board)

		if self.message:
			self.screen.blit(self.text_surface_obj, self.text_rect_obj)

		pygame.display.update()
		self.clock.tick(self.fps)

	def draw_board_squares(self, board):
		"""
		Takes a board object and draws all of its squares to the display
		"""
		for x in range(8):
			for y in range(8):
				pygame.draw.rect(self.screen, board[x][y].color, (x * self.square_size, y * self.square_size, self.square_size, self.square_size), )
	
	def draw_board_pieces(self, board):
		"""
		Takes a board object and draws all of its pieces to the display
		"""
		for x in range(8):
			for y in range(8):
				if board.matrix[x][y].occupant != None:
					pygame.draw.circle(self.screen, board.matrix[x][y].occupant.color, self.pixel_coords((x,y)), self.piece_size) 

					if board.location((x,y)).occupant.king == True:
						pygame.draw.circle(self.screen, GOLD, self.pixel_coords((x,y)), int (self.piece_size / 1.7), self.piece_size >> 2)


	def pixel_coords(self, board_coords):
		"""
		Takes in a tuple of board coordinates (x,y) 
		and returns the pixel coordinates of the center of the square at that location.
		"""
		return (board_coords[0] * self.square_size + self.piece_size, board_coords[1] * self.square_size + self.piece_size)

	def board_coords(self, pixel):
		"""
		Does the reverse of pixel_coords(). Takes in a tuple of of pixel coordinates and returns what square they are in.
		"""
		return (pixel[0] // self.square_size, pixel[1] // self.square_size)

	def highlight_squares(self, squares, origin):
		"""
		Squares is a list of board coordinates. 
		highlight_squares highlights them.
		"""
		for square in squares:
			pygame.draw.rect(self.screen, HIGH, (square[0] * self.square_size, square[1] * self.square_size, self.square_size, self.square_size))	

		if origin != None:
			pygame.draw.rect(self.screen, HIGH, (origin[0] * self.square_size, origin[1] * self.square_size, self.square_size, self.square_size))

	def draw_message(self, message):
		"""
		Draws message to the screen. 
		"""
		self.message = True
		self.font_obj = pygame.font.Font('freesansbold.ttf', 44)
		self.text_surface_obj = self.font_obj.render(message, True, HIGH, BLACK)
		self.text_rect_obj = self.text_surface_obj.get_rect()
		self.text_rect_obj.center = (self.window_size >> 1, self.window_size >> 1)

class Board:
	def __init__(self):
		self.matrix = self.new_board()

	def new_board(self):
		"""
		Create a new board matrix.
		"""

		# initialize squares and place them in matrix
		matrix = [[None] * 8 for i in range(8)]

		for x in range(8):
			for y in range(8):
				if ((x + y) % 2 != 0):
					matrix[y][x] = Square(WHITE)
				else:
					matrix[y][x] = Square(BLACK)

		# initialize the pieces and put them in the appropriate squares

		for x in range(8):
			for y in range(3):
				if matrix[x][y].color == BLACK:
					matrix[x][y].occupant = Piece(RED)
			for y in range(5, 8):
				if matrix[x][y].color == BLACK:
					matrix[x][y].occupant = Piece(BLUE)

		return matrix
	
	def rel(self, dir, pixel):
		"""
		Returns the coordinates one square in a different direction to pixel.

		===DOCTESTS===

		>>> board = Board()

		>>> board.rel(NORTHWEST, (1,2))
		(0,1)

		>>> board.rel(SOUTHEAST, (3,4))
		(4,5)

		>>> board.rel(NORTHEAST, (3,6))
		(4,5)

		>>> board.rel(SOUTHWEST, (2,5))
		(1,6)
		"""
		(x, y) = pixel
		if dir == NORTHWEST:
			return (x - 1, y - 1)
		elif dir == NORTHEAST:
			return (x + 1, y - 1)
		elif dir == SOUTHWEST:
			return (x - 1, y + 1)
		elif dir == SOUTHEAST:
			return (x + 1, y + 1)
		else:
			return 0

	def adjacent(self, pixel):
		"""
		Returns a list of squares locations that are adjacent (on a diagonal) to pixel.
		"""

		return [self.rel(NORTHWEST, pixel), self.rel(NORTHEAST, pixel),self.rel(SOUTHWEST, pixel),self.rel(SOUTHEAST, pixel)]

	def location(self, pixel):
		"""
		Takes a set of coordinates as arguments and returns self.matrix[x][y]
		This can be faster than writing something like self.matrix[coords[0]][coords[1]]
		"""
		(x, y) = pixel

		return self.matrix[x][y]

	def blind_legal_moves(self, pixel):
		"""
		Returns a list of blind legal move locations from a set of coordinates pixel on the board. 
		If that location is empty, then blind_legal_moves() return an empty list.
		"""

		(x, y) = pixel
		if self.matrix[x][y].occupant != None:
			if self.matrix[x][y].occupant.king == False and self.matrix[x][y].occupant.color == BLUE:
				blind_legal_moves = [self.rel(NORTHWEST, pixel), self.rel(NORTHEAST, pixel)]
			elif self.matrix[x][y].occupant.king == False and self.matrix[x][y].occupant.color == RED:
				blind_legal_moves = [self.rel(SOUTHWEST, pixel), self.rel(SOUTHEAST, pixel)]
			else:
				blind_legal_moves = [self.rel(NORTHWEST, pixel), self.rel(NORTHEAST, pixel), self.rel(SOUTHWEST, pixel), self.rel(SOUTHEAST, pixel)]
		else:
			blind_legal_moves = []

		return blind_legal_moves

	def legal_moves(self, pixel, hop = False):
		"""
		Returns a list of legal move locations from a given set of coordinates pixel on the board.
		If that location is empty, then legal_moves() returns an empty list.
		"""

		(x, y) = pixel
		blind_legal_moves = self.blind_legal_moves(pixel) 
		legal_moves = []

		if hop == False:
			for move in blind_legal_moves:
				if hop == False:
					if self.on_board(move):
						if self.location(move).occupant == None:
							legal_moves.append(move)
						elif self.location(move).occupant.color != self.location(pixel).occupant.color and self.on_board((move[0] + (move[0] - x), move[1] + (move[1] - y))) and self.location((move[0] + (move[0] - x), move[1] + (move[1] - y))).occupant == None: # is this location filled by an enemy piece?
							legal_moves.append((move[0] + (move[0] - x), move[1] + (move[1] - y)))

		else: # hop == True
			for move in blind_legal_moves:
				if self.on_board(move) and self.location(move).occupant != None:
					if self.location(move).occupant.color != self.location(pixel).occupant.color and self.on_board((move[0] + (move[0] - x), move[1] + (move[1] - y))) and self.location((move[0] + (move[0] - x), move[1] + (move[1] - y))).occupant == None: # is this location filled by an enemy piece?
						legal_moves.append((move[0] + (move[0] - x), move[1] + (move[1] - y)))

		return legal_moves

	def remove_piece(self, pixel):
		"""
		Removes a piece from the board at position pixel. 
		"""
		(x, y) = pixel
		self.matrix[x][y].occupant = None

	def move_piece(self, pixel_start, pixel_end):
		"""
		Move a piece from (start_x, start_y) to (end_x, end_y).
		"""
		(start_x, start_y) = pixel_start
		(end_x, end_y) = pixel_end

		self.matrix[end_x][end_y].occupant = self.matrix[start_x][start_y].occupant
		self.remove_piece(pixel_start)

		self.king(pixel_end)

	def is_end_square(self, coords):
		"""
		Is passed a coordinate tuple (x,y), and returns true or 
		false depending on if that square on the board is an end square.

		===DOCTESTS===

		>>> board = Board()

		>>> board.is_end_square((2,7))
		True

		>>> board.is_end_square((5,0))
		True

		>>>board.is_end_square((0,5))
		False
		"""

		if coords[1] == 0 or coords[1] == 7:
			return True
		else:
			return False

	def on_board(self, pixel):
		"""
		Checks to see if the given square pixel lies on the board.
		If it does, then on_board() return True. Otherwise it returns false.

		===DOCTESTS===
		>>> board = Board()

		>>> board.on_board((5,0)):
		True

		>>> board.on_board(-2, 0):
		False

		>>> board.on_board(3, 9):
		False
		"""

		(x, y) = pixel
		if x < 0 or y < 0 or x > 7 or y > 7:
			return False
		else:
			return True

	def king(self, pixel):
		"""
		Takes in pixel, the coordinates of square to be considered for kinging.
		If it meets the criteria, then king() kings the piece in that square and kings it.
		"""
		(x, y) = pixel
		if self.location(pixel).occupant != None:
			if (self.location(pixel).occupant.color == BLUE and y == 0) or (self.location(pixel).occupant.color == RED and y == 7):
				self.location(pixel).occupant.king = True 

class Piece:
	def __init__(self, color, king = False):
		self.color = color
		self.king = king

class Square:
	def __init__(self, color, occupant = None):
		self.color = color # color is either BLACK or WHITE
		self.occupant = occupant # occupant is a Square object


import socket
from _thread import *
#from threading import Event
import sys
DEFAULT_PORT = 5555
LOCALHOST = "127.0.0.1"

class GameNet:
	def __init__(self, role, port=DEFAULT_PORT, server_ip=LOCALHOST):
		self.role = role
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn=None
		try:
			if role=='server':
				addr = (LOCALHOST, port) # for server side, IP is localhost
				self.socket.bind(addr)
				self.socket.listen(2)
				start_new_thread(self.thread_server, ())
			else:
				print(f"Trying to connect to {server_ip}:{port}...")
				addr = (server_ip, port)
				self.socket.connect(addr)
				start_new_thread(self.thread_worker, (self.socket,))
		except socket.error as e: print(e)

	def thread_server(self):
		print("Waiting for a connection, Server Started")
		while True:
			conn, addr = self.socket.accept()
			print("Connected to:", addr)
			start_new_thread(self.thread_worker, (conn,))
			# exit here if only allow one client connected

	def thread_worker(self, conn):
		self.conn=conn
		print(f"{self.role} side connected")
		while True:
			try:
				recv_data = conn.recv(2048)
				if recv_data:
					print(f"{self.role} received {recv_data}")
					mouse_event = pygame.event.Event(NET_EVENT, data=recv_data)
					pygame.event.post(mouse_event)
				#else: print("Disconnected"); break
			except Exception as e:
				print(e)
				break
		print("Lost connection")
		conn.close()
		self.conn=None

if __name__ == "__main__":
	session = None
	argc = len(sys.argv)
	server_ip = LOCALHOST
	port = DEFAULT_PORT
	if argc>2:
		m = re.match(r'(([^:]+):)?(\d+)', sys.argv[2])
		if m!=None:
			if m.group(1)!='': server_ip=m.group(2)
			ip = m.group(3)
	if argc>1:
		if sys.argv[1]=='s': session=GameNet('server', port)
		else: session=GameNet('client', port, server_ip)
	game = Game(session)
	game.main()
