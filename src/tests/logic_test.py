from helpers.logic import (
    is_cell_within_bounds,
    is_cell_free,
    is_cell_adjacent_to_colour,
    get_cell_colour,
    find_legal_corners,
    find_legal_moves,
    is_move_legal,
    place_piece
)
from helpers.piece import Piece

# Test is_cell_within_bounds
def test_is_cell_within_bounds():
    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    assert is_cell_within_bounds(board, [0, 0]) == True
    assert is_cell_within_bounds(board, [2, 2]) == True
    assert is_cell_within_bounds(board, [3, 3]) == False

# Test is_cell_free
def test_is_cell_free():
    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    assert is_cell_free(board, [0, 0]) == True
    assert is_cell_free(board, [1, 1]) == True
    board[1][1] = 1
    assert is_cell_free(board, [1, 1]) == False

# Test is_cell_adjacent_to_colour
def test_is_cell_adjacent_to_colour():
    board = [
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    assert is_cell_adjacent_to_colour(board, [0, 0], 1) == True
    assert is_cell_adjacent_to_colour(board, [1, 1], 1) == True
    assert is_cell_adjacent_to_colour(board, [1, 0], 1) == False
    assert is_cell_adjacent_to_colour(board, [2, 2], 1) == False

# Test get_cell_colour
def test_get_cell_colour():
    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    assert get_cell_colour(board, [0, 0]) == 0
    board[0][0] = 1
    assert get_cell_colour(board, [0, 0]) == 1

# Test find_legal_corners
def test_find_legal_corners():
    board = [
        [1, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    legal_corners = find_legal_corners(board, 1)
    assert legal_corners == [[1, 1]]

# Test find_legal_moves
def test_find_legal_moves():
    board = [
        [1, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    legal_corners = find_legal_corners(board, 1)
    assert len(legal_corners) == 1
    available_pieces = [
        Piece("I1", 1),
        Piece("I2", 1)
    ]
    legal_moves = find_legal_moves(board, legal_corners, available_pieces, 1)
    assert len(legal_moves) == 3
    available_pieces = [
        Piece("I2", 1)
    ]
    legal_moves = find_legal_moves(board, legal_corners, available_pieces, 1)
    assert len(legal_moves) == 2
    board[1][1] = 1
    legal_corners = find_legal_corners(board, 1)
    assert len(legal_corners) == 3
    legal_moves = find_legal_moves(board, legal_corners, available_pieces, 1)
    assert len(legal_moves) == 0

# Test is_move_legal
def test_is_move_legal():
    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    move = [
        [[1]],
        [0, 0],
        Piece("I1", 1)
    ]
    assert is_move_legal(board, move, 1, [[0, 0]]) == True
    board[0][0] = 1
    move = [
        [[1, 0], [0, 1]],
        [0, 0],
        Piece("I2", 1)
    ]
    assert is_move_legal(board, move, 1, [[0, 0]]) == False

# Test place_piece
def test_place_piece():
    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    move = [
        [[1]],
        [0, 0],
        Piece("I1", 1)
    ]
    board = place_piece(board, 1, move)
    assert board == [
        [1, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]

