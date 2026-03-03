import pytest
from enums import Location, SeatPart, Action, Card, Rank, Suit

# --- Tests for Location ---

def test_location_from_seat():
    # Valid cases
    assert Location.from_seat(1, SeatPart.HAND) == Location.P1_HAND
    assert Location.from_seat(1, SeatPart.TABLEAU) == Location.P1_TABLEAU
    assert Location.from_seat(4, SeatPart.TABLEAU) == Location.P4_TABLEAU
    
    # Invalid cases
    with pytest.raises(ValueError):
        Location.from_seat(0, SeatPart.HAND)  # Seat too low
    with pytest.raises(ValueError):
        Location.from_seat(5, SeatPart.HAND)  # Seat too high

def test_location_properties():
    # Test shared status
    assert Location.P1_HAND.shared is False
    assert Location.P4_TABLEAU.shared is False
    assert Location.STACK.shared is True
    assert Location.DISCARD.shared is True

    # Test player identification
    assert Location.P1_HAND.player == 1
    assert Location.P4_TABLEAU.player == 4
    assert Location.STACK.player is None

    # Test seat_part identification
    assert Location.P1_HAND.seat_part == SeatPart.HAND
    assert Location.P2_TABLEAU.seat_part == SeatPart.TABLEAU
    assert Location.STACK.seat_part is None

# --- Tests for Action ---

def test_action_creation():
    action = Action(source=Location.P1_HAND, target=Location.STACK, count=2)
    assert action.source == Location.P1_HAND
    assert action.target == Location.STACK
    assert action.count == 2
    assert action.cards is None

def test_action_repr():
    # Ensure the string representation looks correct
    action = Action(source=Location.P1_HAND, target=Location.STACK)
    # Check that the string contains expected info
    rep = repr(action)
    assert "source=P1_HAND" in rep
    assert "target=STACK" in rep
