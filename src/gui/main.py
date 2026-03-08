import pygame
import sys

from ..configurations.config import configuration
from ..configurations.constants import BOARD_SIZE, NUM_PLAYERS
from .constants import *
from . import render


CELL_SIZE = configuration.CELL_SIZE

def run(manager):
    # Initialize Pygame
    pygame.init()

    # Constants
    WIDTH = BOARD_SIZE*CELL_SIZE + CELL_SIZE*2
    HEIGHT = BOARD_SIZE*CELL_SIZE + CELL_SIZE*2
    CENTER = [WIDTH//2, HEIGHT//2] # cols, rows
    PLAYERS = manager.player_list

    # Create the Pygame screen
    ICON = pygame.image.load("./src/gui/icon.png")
    pygame.display.set_icon(ICON)
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE)
    pygame.display.set_caption("Blokus")

    # Clear the screen
    SCREEN.fill(WHITE)

    # Main loop
    running = True
    clock = pygame.time.Clock()

    # Initialise
    print(f"Starting Game with {NUM_PLAYERS} players...")
    flag = True
    end_game_check = 0
    round = manager.round

    # Game Loop
    print("Playing...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        grid = manager.board
        SCREEN.fill(WHITE)

        if flag:
            manager.round = manager.turn // NUM_PLAYERS + 1
            if round != manager.round:
                round = manager.round
                end_game_check = 0
            player = PLAYERS[manager.turn % NUM_PLAYERS]
            end_game_check += 1

            if manager.player_turn(player):
                end_game_check = 0

            if end_game_check == NUM_PLAYERS:
                flag = False
                manager.end_game()
        
        render.render_board(SCREEN, grid, CENTER)
        
        # Update the display
        pygame.display.flip()
        clock.tick(30)


    # Quit Pygame
    pygame.quit()
    sys.exit()