import pytest
from unittest.mock import MagicMock, patch
from gameserver import GameServer
from enums import *
from cards import CardSet, Table

@pytest.fixture
def table():
    """Provides a clean Table for testing."""
    return Table(seats=2, empty=True)

def test_execute_draw_stack_to_hand(table):
    """Verify Table moves multiple cards from stack to hand."""
    table.stack.cards = [ACE_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES]

    # Action: Player 1 draws 2
    action = Action(source=STACK, target=P1_HAND, count=2)
    assert table.execute_action(action)

    assert len(table.stack.cards) == 1
    assert len(table.seats[0].hand.cards) == 2
    # Only three is left in deck
    assert THREE_OF_SPADES in table.stack

def test_execute_specific_card_from_discard(table):
    """Verify Table moves a specific named card from discard."""
    table.discard.cards = [FOUR_OF_CLUBS, KING_OF_HEARTS, ACE_OF_DIAMONDS]

    # Action: Player 2 takes the King
    action = Action(source=DISCARD, target=P2_HAND, cards=KING_OF_HEARTS)
    assert table.execute_action(action)

    assert KING_OF_HEARTS not in table.discard.cards
    assert KING_OF_HEARTS in table.seats[1].hand.cards
    assert len(table.discard.cards) == 2

def test_execute_draw_from_stack(table):
    """Test drawing multiple cards from the stack to a player's hand."""
    # Setup: Put 3 cards in the stack
    table.stack.cards = [ACE_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES]
    
    # Action: Player 1 draws 2 cards
    action = Action(source=STACK, target=P1_HAND, count=2)
    assert table.execute_action(action)
    
    # Assertions
    assert len(table.stack.cards) == 1
    assert len(table.seats[0].hand.cards) == 2
    # Verify the specific cards moved (assuming .draw() takes from the end/top)
    assert ACE_OF_SPADES in table.seats[0].hand.cards
    assert TWO_OF_SPADES in table.seats[0].hand.cards

def test_execute_move_specific_card(table):
    """Test picking up a specific card from the discard pile."""
    # Setup: Put a specific card on the discard pile
    target_card = KING_OF_HEARTS
    table.discard.cards = [FOUR_OF_CLUBS, target_card]
    
    # Action: Player 2 takes the King of Hearts
    action = Action(
        source=DISCARD, 
        target=P2_HAND, 
        cards=target_card
    )
    assert table.execute_action(action)
    
    # Assertions
    assert target_card not in table.discard.cards
    assert target_card in table.seats[1].hand.cards
    assert len(table.discard.cards) == 1

def test_execute_tableau_move(table):
    """Test moving a card from hand to tableau (playing a card)."""
    # Setup: Player 1 has a card in hand
    table.seats[0].hand.cards = [TEN_OF_DIAMONDS]
    
    # Action: Move card to Tableau
    action = Action(
        source=P1_HAND, 
        target=P1_TABLEAU, 
        cards=TEN_OF_DIAMONDS
    )
    assert table.execute_action(action)
    
    # Assertions
    assert TEN_OF_DIAMONDS not in table.seats[0].hand.cards
    assert TEN_OF_DIAMONDS in table.seats[0].tableau.cards

def test_execute_empty_source_fails(table):
    """Verify Table raises ValueError when source is empty."""
    table.stack.cards = []
    action = Action(source=STACK, target=P1_HAND, count=1)

    assert not table.execute_action(action)

def test_execute_insufficient_cards(table, capsys):
    """Test behavior when the source has fewer cards than the action count."""
    # Setup: Stack only has 1 card
    table.stack.cards = [ACE_OF_CLUBS]
    
    # Action: Player 1 tries to draw 5
    action = Action(source=STACK, target=P1_HAND, count=2)
    assert not table.execute_action(action)
    
    # Assertions: Should draw at all
    assert len(table.seats[0].hand.cards) == 0 
    assert len(table.stack.cards) == 1

def test_invalid_card_not_in_source(table, capsys):
    """Test behavior when the specific card requested isn't in the source."""
    # Setup: Discard has a different card
    table.discard.cards = [TWO_OF_HEARTS]
    
    # Action: Try to take a card that isn't there
    action = Action(
        source=DISCARD, 
        target=P1_HAND, 
        cards=ACE_OF_SPADES
    )
    assert not table.execute_action(action)
    
    # Assertions
    assert len(table.seats[0].hand.cards) == 0
