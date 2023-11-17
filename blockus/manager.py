# Import
import random
import time
import copy

from . import logic
from .helpers.piece import Piece
from .player import Player
from .helpers import draw

VERBOSITY = True
DRAW = False
DRAW_RESULTS = False
STEP_BY_STEP = False
MAX_ROUNDS = -1
ALL_PIECES = ["I1", "I2", "I3", "I4", "I5", "V3", "O4", "Z4", "T4", "L4", "U", "P", "Y", "L5", "N", "X", "W", "F", "T", "V5", "Z5"]

class Manager:
    def __init__(self, no_of_players, available_pieces_types = ALL_PIECES, ai_versions = None):
        # Initialise Game
        self.round = 0
        self.turn = 1
        # Check if input values are correct
        
        # If AI versions aren't specified
        if ai_versions is None:
            self.ai_versions = ["v1" for player in range(1,no_of_players+1)]

        self.ai_versions = ai_versions

        # Players
        if not (2 <= no_of_players <= 4):
            raise ValueError("Must be 2-4 players")
        self.no_of_players = no_of_players
        self.player_list = [Player(player, self.ai_versions[player-1]) for player in range(1,no_of_players+1)]

        # Generate Board
        self.board_size = 3*no_of_players + 8
        self.board = [[ 0 for x in range(0,self.board_size)] for y in range(0,self.board_size)]

        # Generate Pieces for players
        self.player_pieces = []
        for player in range(1,no_of_players+1):
            self.player_pieces.append([Piece(piece_type,player) for piece_type in available_pieces_types])
        

    def start_game(self):
        print(f"Starting Game with {self.no_of_players} players...")
        flag = True
        # Game Loop
        print("Playing...")
        timer = time.time()
        while(flag):
            self.round += 1
            self.output_text(f"Round: {self.round}")
            flag = False
            for player in self.player_list:
                if self.player_turn(player):
                    flag = True

            if STEP_BY_STEP: 
                draw._board(self.board)
                input("")
            if self.round == MAX_ROUNDS: break
        timer = format(time.time()-timer,".2f")
        print(f"Game finished after {timer}s") # Print how long game took
        self.end_game()

    def end_game(self):
        print("Showing results...")

        print(f"Played a total of {self.round} rounds")

        if DRAW_RESULTS:
            # Show final state of board
            draw._board(self.board)
            # Show Remaining Pieces
            self.output_text("\nRemaining Pieces:")
            for pieces in self.player_pieces:
                pieces_list = [_.piece for _ in pieces]
                draw._pieces_in_row(pieces_list)

        # Show Results
        results = logic.get_results(self.player_list, self.player_pieces)
        draw._results(results)
        

    def player_turn(self, player):
        player_string = draw.render_cell(player.colour, str(player))

        # If player finished -> End Turn
        if player.finished:
            self.output_text(f"{player_string} is finished...")
            return False

        # If no pieces left -> End Turn
        available_pieces = self.player_pieces[player.colour-1]
        if len(available_pieces) == 0:
            player.finished = True
            self.output_text(f"{player_string} has no more pieces...")
            return False
        
        if DRAW: 
            print(f"{player_string}'s available pieces:")
            draw._pieces_in_row([_.piece for _ in available_pieces])

        if self.round == 1:
            # Get starting squares
            match player.colour:
                case 1: # Red starts in top-left
                    legal_corners = [[0,0]]
                case 2: # Green starts in bottom-left but bottom-right if there are only 2 players
                    if self.no_of_players != 2:
                        legal_corners = [[self.board_size-1,0]]
                    else:
                        legal_corners = [[self.board_size-1,self.board_size-1]]
                case 3: # Yellow starts in bottom-right
                    legal_corners = [[self.board_size-1,self.board_size-1]]
                case 4: # Blue starts in top-right
                    legal_corners = [[0,self.board_size-1]]
                case _:
                    raise ValueError("Invalid Colour")
        else:
            # If no corners to place piece -> End Turn
            legal_corners = logic.find_legal_corners(self.board, player.colour)
            if len(legal_corners) == 0:
                player.finished = True
                self.output_text(f"{player_string} has no legal moves...")
                return False
        
        # Get all possible moves
        legal_moves = logic.find_legal_moves(self.board, legal_corners, available_pieces, player.colour)
        # If no legal moves -> End Turn
        if len(legal_moves) == 0: 
            player.finished = True
            self.output_text(f"{player_string} has no legal moves...")
            return False
        
        # Get Move
        final_move = player.generate_move(legal_moves, self.board, self.round)
       
        self.output_text(f"{player_string} placed {final_move[2]} at {final_move[1]}")
        if DRAW:
            draw._piece(final_move[0])

        # Remove piece from available pieces
        self.player_pieces[player.colour-1].remove(final_move[2])

        # Place piece
        self.board = logic.place_piece(self.board, player.colour, final_move)

        # End Turn
        self.turn += 1
        return True
    
    def output_text(self, text):
        if VERBOSITY: print(text)


