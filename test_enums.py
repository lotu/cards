import pytest
from enums import *

# --- Tests for Location ---

def test_location_from_seat():
    # Valid cases
    assert Location.from_seat(1, SeatPart.HAND) == P1_HAND
    assert Location.from_seat(PLAYER_1, SeatPart.HAND) == P1_HAND
    assert Location.from_seat(PLAYER_1, SeatPart.TABLEAU) == P1_TABLEAU
    assert Location.from_seat(PLAYER_4, SeatPart.TABLEAU) == P4_TABLEAU
    assert Location.from_seat(4, SeatPart.TABLEAU) == P4_TABLEAU
    
    # Invalid cases
    with pytest.raises(ValueError):
        Location.from_seat(0, SeatPart.HAND)  # Seat too low
    with pytest.raises(ValueError):
        Location.from_seat(5, SeatPart.HAND)  # Seat too high

def test_location_properties():
    # Test shared status
    assert P1_HAND.shared is False
    assert P4_TABLEAU.shared is False
    assert STACK.shared is True
    assert DISCARD.shared is True

    # Test player identification
    assert P1_HAND.player == PLAYER_1
    assert P4_TABLEAU.player == PLAYER_4
    assert STACK.player is None

    # Test seat_part identification
    assert P1_HAND.seat_part == SeatPart.HAND
    assert P2_TABLEAU.seat_part == SeatPart.TABLEAU
    assert STACK.seat_part is None

# --- Tests for CardMove ---

def test_card_move_creation():
    card_move = CardMove(source=P1_HAND, target=STACK, count=2)
    assert card_move.source == P1_HAND
    assert card_move.target == STACK
    assert card_move.count == 2
    assert card_move.cards is None

def test_card_move_repr():
    # Ensure the string representation looks correct
    card_move = CardMove(source=P1_HAND, target=STACK)
    # Check that the string contains expected info
    rep = repr(card_move)
    assert "source=P1_HAND" in rep
    assert "target=STACK" in rep

@pytest.mark.parametrize("source, target, count, cards, expected_snippet", [
    # Basic Drawing
    (STACK, P1_HAND, 1, None, "draws 1 card from the stack to Player 1's hand"),
    
    # Drawing multiple
    (STACK, P1_HAND, 3, None, "draws 3 cards from the stack to Player 1's hand"),
    
    # Discarding a specific card
    (P2_HAND, DISCARD, 1, ACE_OF_SPADES, "discards A♠ from Player 2's hand to the discard"),
    
    # Moving within own area (Hand to Tableau)
    (P3_HAND, P3_TABLEAU, 1, None, "moves 1 card from Player 3's hand to Player 3's tableau"),

    # Moving within own area (Hand to Tableau)
    (None, P3_TABLEAU, 1, TWO_OF_SPADES, "moves 2♠ from anywhere to Player 3's tableau"),
    (P2_HAND, None, 1, None, "moves 1 card from Player 2's hand to unknown"),

    (STACK, DISCARD, 1, None, "draws 1 card from the stack to the discard"), # XXX
    
    # Playing to someone else's tableau
    (P1_HAND, P2_TABLEAU, 1, TEN_OF_DIAMONDS, "moves T♢ from Player 1's hand to Player 2's tableau"),
    
    (P2_HAND, DISCARD, 1, None, "discards 1 card from Player 2's hand to the discard"),
    # Handling a list of cards
    (P4_HAND, DISCARD, 2, [TWO_OF_CLUBS, THREE_OF_CLUBS], 
     "discards 2♣, 3♣ from Player 4's hand to the discard"),
])
def test_card_move_descriptions(source, target, count, cards, expected_snippet):
    """Verifies that CardMove.describe() produces the correct natural language string."""
    card_move = CardMove(source=source, target=target, count=count, cards=cards)
    
    result = card_move.__str__()
    
    # We check if the expected string is exactly the result
    assert result == expected_snippet

def test_player():
    assert PLAYER_1.value == 0
    assert PLAYER_1.num == 1
    assert PLAYER_1.idx == 0
    assert str(PLAYER_1) == "Player 1"

    assert PlayerId.from_num(2) == PLAYER_2
    assert PlayerId.from_index(2) == PLAYER_3
    
    assert PLAYER_4.value == 3
    assert PLAYER_4.num == 4
    assert str(PLAYER_4) == "Player 4"
