import pytest
from gameserver import  interpret_input
from cards import Table, CardSet
from enums import *

@pytest.fixture
def table():
    """Provides a clean Table for testing."""
    return Table(seats=2, empty=True)

# --- interpret_input Tests ---

def test_interpret_draw_command(table):
    """Verify string 'draw 3' translates to correct Action object."""
    # Player 1 (idx 0)
    action = interpret_input("draw 3", 0, table)

    assert action.source == STACK
    assert action.target == P1_HAND
    assert action.count == 3
    assert action.cards is None

def test_interpret_discard_command(table):
    """Verify string 'get from discard' translates to correct Action."""
    action = interpret_input("take from pile", 1, table)

    assert action.source == DISCARD
    assert action.target == P2_HAND

def test_interpret_specific_card_logic(table):
    """Verify naming a card on top of discard creates a specific Action."""
    top_card = ACE_OF_SPADES
    table.discard.cards = [TWO_OF_CLUBS, top_card]

    # Note: interpret_input uses your parse_card logic
    action = interpret_input("Ace of Spades", 0, table)

    assert action.source == DISCARD
    assert action.cards == top_card

# --- Integrated Logic Test ---

def test_full_logic_loop(table):
    """Test the flow from string -> Action -> Table update."""
    table.stack.cards = [JACK_OF_DIAMONDS]

    # 1. Interpret
    action = interpret_input("draw 1", 0, table)

    # 2. Execute
    table.execute_action(action)

    # 3. Verify
    assert len(table.stack.cards) == 0
    assert JACK_OF_DIAMONDS in table.seats[0].hand.cards

def test_interpret_draw_basic(table):
    """Verify 'draw' keyword defaults to stack and correct player hand."""
    # Player 1 (idx 0)
    action = interpret_input("draw", 0, table)
    assert isinstance(action, Action)
    assert action.source == STACK
    assert action.target == P1_HAND
    assert action.count == 1

    # Player 2 (idx 1)
    action = interpret_input("hit", 1, table)
    assert action.target == P2_HAND

def test_interpret_draw_with_count(table):
    """Verify numeric extraction from strings like 'draw 3'."""
    action = interpret_input("draw 5 cards", 0, table)
    assert action.count == 5
    assert action.source == STACK

def test_interpret_draw_from_discard(table):
    """Verify keywords like 'discard' or 'pile' switch the source."""
    action = interpret_input("take from discard", 0, table)
    assert action.source == DISCARD
    
    action = interpret_input("get from pile", 0, table)
    assert action.source == DISCARD

def test_interpret_specific_card_name( table):
    """Verify that naming the top discard card generates a specific Action."""
    target_card = ACE_OF_SPADES
    table.discard.cards = [TWO_OF_CLUBS, ACE_OF_SPADES]
    
    # Input matches the top card of discard
    action = interpret_input("Ace of Spades", 0, table)
    assert action.source == DISCARD
    assert action.cards == target_card

def test_interpret_specific_card_not_on_top(table):
    """Verify that naming a card NOT on top of discard doesn't trigger a draw."""
    table.discard.cards = [KING_OF_HEARTS] # Top is King
    
    # User asks for Ace (which isn't there)
    # This should fail the 'target_card == discard[-1]' check and return None 
    # or fall back to general draw if 'draw' is in the text.
    action = interpret_input("Ace of Spades", 0, table)
    assert action is None

def test_interpret_garbage_input(table):
    """Verify that unrelated text returns None."""
    assert interpret_input("hello?", 0, table) is None
    assert interpret_input("pass", 0, table) is None
    assert interpret_input("", 0, table) is None
