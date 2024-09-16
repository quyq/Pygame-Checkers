Pygame-Checkers
===============

GitHub repository for an individual project in Python for Programming Workshop at Marlboro College. The goal was to create a fully functional checkers engine for two players.

User should install pygame 1.9.2 release for required libraries. 


Note about implementation
=========================
It has 5 class defined:
Game:
  event_loop
Graphics:
  drawing operation
Board:
  Has a 8X8 matrix, each elment is a Square with color white or black.
  new_board: init matrix with color
  board_string: return a matrix of string of color. For test only, not useful
  rel: return coordinate of adjacent square, based on direction
  adjacent: return all 4 coordinates of all 4 directions
  location: return Square of the matrix at the coordinate
  blind_legal_moves: return list of blind legal move locations
  legal_moves: return list of legal move locations, i.e. include hopable
  remove_piece: remove piece (for hop)
  move_piece: move piece and check king state
  is_end_saure: check whether the given sqaure is on end of board
  on_board: check the given square is on the board
  king: check whether the squre is kinging
Piece:
  Only has two members: color and king
Squre:
  Only has two members: color and occupant
