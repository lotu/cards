import asyncio
import os
import pytest
import shutil
from cards import *
from gameserver import *
from enums import *

FIFO_TEST_DIR = "test_fifo"

@pytest.fixture(scope="function")
def setup_fifos():
    """Fixture to create and cleanup FIFOs for each test."""
    if os.path.exists(FIFO_TEST_DIR):
        shutil.rmtree(FIFO_TEST_DIR)
    os.makedirs(FIFO_TEST_DIR)
    
    player_count = 2
    anchors = []
    
    for i in range(1, player_count + 1):
        in_p = os.path.join(FIFO_TEST_DIR, f"p{i}_in")
        out_p = os.path.join(FIFO_TEST_DIR, f"p{i}_out")
        os.mkfifo(in_p)
        os.mkfifo(out_p)
        
        # O_RDWR acts as our 'anchor' so writers don't block on open
        anchors.append(os.open(in_p, os.O_RDWR))
        anchors.append(os.open(out_p, os.O_RDWR))
        
    yield player_count, FIFO_TEST_DIR
    
    for fd in anchors:
        os.close(fd)
    if os.path.exists(FIFO_TEST_DIR):
        shutil.rmtree(FIFO_TEST_DIR)

@pytest.mark.asyncio
async def test_player_input_capture(setup_fifos):
    """Test that wait_for_input only returns when a newline is sent."""
    count, folder = setup_fifos
    player = FIFOPlayer(PLAYER_1, folder)
    player.connect()
    
    # Wrap wait_for_input in a task
    input_task = asyncio.create_task(player.wait_for_input())
    
    # Check that it's still waiting
    done, pending = await asyncio.wait([input_task], timeout=0.1)
    assert len(done) == 0
    
    # Send partial data
    os.write(os.open(player.in_path, os.O_WRONLY), b"Hel")
    
    done, pending = await asyncio.wait([input_task], timeout=0.1)
    assert len(done) == 0
    
    # Send newline
    os.write(os.open(player.in_path, os.O_WRONLY), b"lo\n")
    
    result = await asyncio.wait_for(input_task, timeout=1.0)
    assert result == "Hello"

@pytest.mark.asyncio
async def test_server_waits_for_all(setup_fifos):
    """Verify server doesn't advance turn until the LAST player speaks."""
    count, folder = setup_fifos
    server = GameServer(player_count=count, fifo_dir=folder, test=True)
    for p in server.players:
        p.connect()

    # Coroutine wrapper to avoid TypeError: a coroutine was expected, got <_GatheringFuture pending>
    async def gather_inputs():
        return await asyncio.gather(*(p.wait_for_input() for p in server.players))

    gather_task = asyncio.create_task(gather_inputs())

    # Player 1 responds
    os.write(os.open(server.players[0].in_path, os.O_WRONLY), b"Ready\n")

    # Verify task is still pending (Waiting for Player 2)
    done, pending = await asyncio.wait([gather_task], timeout=0.2)
    assert len(done) == 0

    # Player 2 responds
    os.write(os.open(server.players[1].in_path, os.O_WRONLY), b"Go\n")

    # Now it should resolve
    results = await asyncio.wait_for(gather_task, timeout=1.0)
    assert results == ["Ready", "Go"]

@pytest.mark.asyncio
async def test_broadcast_turn(setup_fifos):
    """Verify data written by the server is readable from the out pipe."""
    count, folder = setup_fifos
    server = GameServer(player_count=count, fifo_dir=folder, test=True)
    for p in server.players:
        p.connect()
        
    test_msg = "Turn Start"
    for p in server.players:
        p.send_message(test_msg)
        
    # Read and verify
    for p in server.players:
        # Open for reading in non-blocking mode to check buffer
        fd = os.open(p.out_path, os.O_RDONLY | os.O_NONBLOCK)
        data = os.read(fd, 1024).decode()
        os.close(fd)
        assert test_msg in data
