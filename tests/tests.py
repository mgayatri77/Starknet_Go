import pytest
import random
from starkware.starknet.testing.starknet import Starknet
from timeit import default_timer as timer
from enum import Enum

class States(Enum): 
    P1_TURN = 0
    P2_TURN = 1
    GAME_OVER = 2
    GAME_NOT_STARTED = 3

GRIDX, GRIDY = 9, 9
CONTRACT = "../Go.cairo"

@pytest.mark.asyncio
async def test_game_initialization():
    starknet = await Starknet.empty()
    contract = await starknet.deploy(CONTRACT)

    # start game with P1 and check game state
    await contract.start_game(GRIDX, GRIDY).execute()
    (game_state) = await contract.get_game_state().call()
    assert game_state.result.state == States.GAME_NOT_STARTED.value
    
    # join game as P2 and check game state
    await contract.join().execute()
    (game_state) = await contract.get_game_state().call()
    assert game_state.result.state == States.P1_TURN.value

@pytest.mark.asyncio
async def test_valid_move():
    starknet = await Starknet.empty()
    contract = await starknet.deploy(CONTRACT)
    
    # start game with P1 and P2 and check game state
    await contract.start_game(GRIDX, GRIDY).execute()
    await contract.join().execute()

    # make random move as player 1
    rx, ry = random.randint(0, GRIDX-1), random.randint(0, GRIDY-1)
    pmove = await contract.player_move(rx, ry, States.P1_TURN.value).execute()
    board = await contract.get_board_at(rx, ry).call()

    # check for success and update
    assert (pmove.result.valid == True)
    assert (board.result.value == 0)

@pytest.mark.asyncio
async def test_capture ():
    starknet = await Starknet.empty()
    contract = await starknet.deploy(CONTRACT)
    
    # start game with P1 and P2 and check game state
    await contract.start_game(GRIDX, GRIDY).execute()
    await contract.join().execute()

    # define moves
    moves = [(2, 0), (4, 0), (2, 1), (4, 1), (2, 2), (4, 2), 
             (2, 3), (4, 3), (1, 3), (4, 4), (0, 4), (4, 5), 
             (6, 0), (4, 6), (8, 0), (4, 7), (3, 5), (2, 7), 
             (3, 6), (2, 8), (3, 7), (7, 3), (3, 8), (7, 4), 
             (2, 6), (7, 5), (1, 7), (5, 6), (1, 8), (5, 8)]

    # define expected board after moves
    expected_board = [[0, 0, 0, 0, 1, 0, 0, 0, 0],
                     [0, 0, 0, 1, 0, 0, 0, 1, 1],
                     [1, 1, 1, 1, 0, 0, 1, 0, 0],
                     [0, 0, 0, 0, 0, 1, 1, 1, 1],
                     [2, 2, 2, 2, 2, 2, 2, 2, 0],
                     [0, 0, 0, 0, 0, 0, 2, 0, 2],
                     [1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 2, 2, 2, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0, 0, 0]]
    
    # execute moves
    for i in range(len(moves)): 
        nx, ny = moves[i]
        pmove = await contract.player_move(nx, ny, i % 2).execute()
        assert (pmove.result.valid == True)
    
    # compare expected grid and actual grid
    actual_board = [[_ for i in range(GRIDY)] for _ in range(GRIDX)]
    for i in range(GRIDX): 
        for j in range(GRIDY): 
            curr_val = await contract.get_board_at(i, j).call()
            actual_board[i][j] = curr_val.result.value
    
    for i in range(GRIDX): 
        for j in range(GRIDY): 
            curr_val = await contract.get_board_at(i, j).call()
            expected_val = expected_board[i][j]-1 if (expected_board[i][j] > 0) else 2
            assert curr_val.result.value == expected_val