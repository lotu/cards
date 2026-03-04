import pytest
from unittest.mock import MagicMock, patch
from enums import *
from cards import CardSet, Table

@pytest.fixture
def table():
    """Provides a clean Table for testing."""
    return Table(seats=2, empty=True)

@pytest.mark.parametrize("action, setup_cards, expected_source_len, expected_target_len", [
    # Scenario 1: Player 1 plays a card from hand to their own tableau
    (
        Action(source=P1_HAND, target=P1_TABLEAU, cards=ACE_OF_SPADES),
        {P1_HAND: [ACE_OF_SPADES], P1_TABLEAU: []},
        0, 1
    ),
    # Move with card set not properlly done XXX
    # # Scenario 1: Player 1 plays a card from hand to their own tableau
    # (
    #     Action(source=P1_HAND, target=P1_TABLEAU, cards=[ACE_OF_SPADES]),
    #     {P1_HAND: [ACE_OF_SPADES], P1_TABLEAU: []},
    #     0, 1
    # ),

    # # Scenario 2: Player 1 takes 1 random card from Player 2's hand
    (
        Action(source=P2_HAND, target=P1_HAND, count=1),
        {P2_HAND: [KING_OF_CLUBS, QUEEN_OF_CLUBS], P1_HAND: []},
        1, 1
    ),
    # Scenario 3: Player 1 steals a specific card from Player 2's tableau
    (
        Action(source=P2_TABLEAU, target=P1_HAND, cards=TEN_OF_DIAMONDS),
        {P2_TABLEAU: [TEN_OF_DIAMONDS], P1_HAND: []},
        0, 1
    ),
])
def test_execute_player_moves(table, action, setup_cards, expected_source_len, expected_target_len):
    """Verify Table.execute_action correctly moves cards between player zones."""
    # 1. Setup the state
    for loc, card_list in setup_cards.items():
        # Using the helper you wrote for the Table class
        cardset = table._get_cardset(loc)
        cardset.cards = list(card_list)

    # 2. Execute
    table.execute_action(action)

    # 3. Verify
    assert len(table._get_cardset(action.source).cards) == expected_source_len
    assert len(table._get_cardset(action.target).cards) == expected_target_len

    # If a specific card was moved, verify it's in the target
    if action.cards:
        assert action.cards in table._get_cardset(action.target).cards

# --- Test Execution of Complex Interactions ---

@pytest.mark.parametrize("action, setup_data", [
    # Scenario: P1 steals from P2's hand
    (
        Action(source=P2_HAND, target=P1_HAND, count=1),
        {P2_HAND: [ACE_OF_SPADES], P1_HAND: []}
    ),
    # Scenario: P1 plays specific card to own tableau
    (
        Action(source=P1_HAND, target=P1_TABLEAU, cards=KING_OF_HEARTS),
        {P1_HAND: [KING_OF_HEARTS], P1_TABLEAU: []}
    ),
    # Scenario: P2 gives a card to P1's tableau
    (
        Action(source=P2_HAND, target=P1_TABLEAU, cards=TEN_OF_DIAMONDS),
        {P2_HAND: [TEN_OF_DIAMONDS], P1_TABLEAU: []}
    ),
])

def test_execute_interaction_movement(table, action, setup_data):
    # Setup initial card states
    for location, cards in setup_data.items():
        table._get_cardset(location).cards = list(cards)
    
    # Execute
    table.execute_action(action)
    
    # Verify target has the cards
    target_set = table._get_cardset(action.target)
    if action.cards:
        assert action.cards in target_set.cards
    else:
        assert len(target_set.cards) == action.count
    
    # Verify source is empty (in these specific 1-card scenarios)
    assert len(table._get_cardset(action.source).cards) == 0


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


