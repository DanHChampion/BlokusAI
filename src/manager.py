# Import
import time
import random

from .configurations.config import configuration
from .configurations.constants import BOARD_SIZE, NUM_PLAYERS, ALL_PIECES
from .helpers import logic
from .helpers.piece import Piece
from .helpers.player import Player
from .helpers import draw

VERBOSITY = configuration.VERBOSITY
DRAW = configuration.DRAW
DRAW_RESULTS = configuration.DRAW_RESULTS
STEP_BY_STEP = configuration.STEP_BY_STEP
RECORD = configuration.RECORD

class Manager:
    def __init__(self, ai_versions, shuffle = False):
        self.intialise(ai_versions, shuffle)
        
    def intialise(self, ai_versions, shuffle):
        # Initialise Game
        self.round = 0
        self.turn = 0
        
        # Players
        self.no_of_players = NUM_PLAYERS

        # Validate AI versions
        self.ai_versions = ai_versions
        if len(self.ai_versions) != self.no_of_players:
            raise ValueError(f"Expected {self.no_of_players} AI versions, but got {len(self.ai_versions)}.")
        if any(ai_version == "hm" for ai_version in self.ai_versions):
            raise ValueError("Invalid AI version: 'hm' is only allowed for GAME phase.")
        
        self.player_list = [Player(player, self.ai_versions[player-1]) for player in range(1,self.no_of_players+1)]
        
        if shuffle:
            shift = random.randint(1, self.no_of_players)
            self.player_list = self.player_list[shift:] + self.player_list[:shift]

        # Generate Board
        self.board_size = BOARD_SIZE
        self.board = [[ 0 for x in range(0,self.board_size)] for y in range(0,self.board_size)]

        # Generate Pieces for players
        self.available_pieces_types = ALL_PIECES
        self.player_pieces = []
        for player in self.player_list:
            player.remaining_pieces = [Piece(piece_type,player.colour) for piece_type in ALL_PIECES]

        self.start_time = time.time()


    def start_game(self):
        print(f"Starting game...")
        flag = True
        # Game Loop
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
        self.end_game()

    def end_game(self):
        runtime = format(time.time()-self.start_time,".2f")
        print("Showing results...")
        print(f"Game finished after {runtime}s")
        print(f"Played a total of {self.round} rounds")

        if DRAW_RESULTS:
            # Show final state of board
            draw._board(self.board)
            # Show Remaining Pieces
            self.output_text("\nRemaining Pieces:")
            for player in self.player_list:
                pieces_list = [_.piece for _ in player.remaining_pieces]
                draw._pieces_in_row(pieces_list)

        # Show Results
        results = self.get_results()
        draw._results(results)
        

    def player_turn(self, player):
        player_string = draw.render_cell(player.colour, str(player))
        self.turn += 1

        # If player finished -> End Turn
        if player.finished:
            self.output_text(f"{player_string} is finished...")
            return False

        # If no pieces left -> End Turn
        available_pieces = player.remaining_pieces
        if len(available_pieces) == 0:
            player.finished = True
            self.output_text(f"{player_string} has no more pieces...")
            return False
        
        if DRAW: 
            print(f"{player_string}'s available pieces:")
            draw._pieces_in_row([_.piece for _ in available_pieces])

        if self.round == 1:
            # Get starting squares
            legal_corners = logic.get_starting_corner(self.board_size, player.colour)
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
        
        # Get Move -> move = [orientation, cell, piece]
        final_move = player.generate_move(legal_moves, self.board, self.round)
       
        self.output_text(f"{player_string} placed {final_move[2]} at {final_move[1]}")
        if DRAW:
            draw._piece(final_move[0])

        # Remove piece from available pieces
        player.remaining_pieces.remove(final_move[2])

        # Place piece
        self.board = logic.place_piece(self.board, player.colour, final_move)

        # End Turn
        return True
    
    def output_text(self, text):
        if VERBOSITY: print(text)

    def get_results(self):
        return logic.calc_results(self.player_list)


