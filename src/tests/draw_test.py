from helpers.draw import render_cell, _piece, _pieces_in_row, _board, _results
from colorama import Fore, Style
from helpers.piece import Piece

# Test for render_cell function
def test_render_cell_red():
    assert render_cell(1) == f"{Fore.RED}■{Style.RESET_ALL}"

def test_render_cell_green():
    assert render_cell(2) == f"{Fore.GREEN}■{Style.RESET_ALL}"

def test_render_cell_yellow():
    assert render_cell(3) == f"{Fore.YELLOW}■{Style.RESET_ALL}"

def test_render_cell_blue():
    assert render_cell(4) == f"{Fore.BLUE}■{Style.RESET_ALL}"

def test_render_cell_default():
    assert render_cell(0) == "   "

def test_render_cell_debug():
    assert render_cell('D') == " # "

# Test for _piece function (capturing printed output)
def test_piece_output(capfd):
    piece = [[1, 0], [0, 1]]
    _piece(piece)
    captured = capfd.readouterr()
    assert "■" in captured.out  # Checks for the printed cell output
    assert "   " in captured.out  # Checks for empty cells

# Test for _pieces_in_row function (capturing printed output)
def test_pieces_in_row(capfd):
    pieces = [
        [[1, 0], [0, 1]],
        [[1, 0], [0, 1]]
    ]
    _pieces_in_row(pieces)
    captured = capfd.readouterr()
    assert "■" in captured.out  # Checking for printed block
    assert "   " in captured.out  # Checking for empty cells

# Test for _board function (capturing printed output)
def test_board_output(capfd):
    data = [
        [1, 2, 3],
        [3, 0, 1],
        [0, 0, 4]
    ]
    _board(data)
    captured = capfd.readouterr()
    assert "+---+---+" in captured.out  # Checking for the board's row delimiters
    assert "███" in captured.out  # Checking for rendered coloured cells
    assert "|"+ " " * 3 in captured.out  # Ensures cell formatting

# Test for _results function (capturing printed output)
def test_results_output(capfd):
    data = [
        ("Red", 1, 10, "v1", [Piece("L5",1), Piece("Y",1)]),
        ("Blue", 4, 14, "v2", [Piece("P",4), Piece("F",4),Piece("L4",4)])
    ]
    _results(data)
    captured = capfd.readouterr()
    
    # Check for proper table headers
    assert "| Player" in captured.out
    assert "| Score" in captured.out
    assert "| AI Version" in captured.out
    assert "| Remaining Pieces" in captured.out

    # Check for row data
    assert f"| {Fore.RED}Red{Style.RESET_ALL}" in captured.out
    assert f"| {Fore.BLUE}Blue{Style.RESET_ALL}" in captured.out
    assert "10" in captured.out
    assert "14" in captured.out
    assert "v1" in captured.out
    assert "v2" in captured.out
