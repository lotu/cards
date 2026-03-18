import pytest
from gameserver import  interpret_input
from enums import *

# --- Test Parsing of Complex Interactions ---

@pytest.mark.parametrize("text, player_idx, expected_source, expected_target, expected_card, expected_count", [
    # Playing to own tableau
    ("play Ace of Spades", 0, None, P1_TABLEAU, [ACE_OF_SPADES], 1),
    ("put King of Hearts on table", 1, None, P2_TABLEAU, [KING_OF_HEARTS], 1),

    # Taking from other players
    ("take from p2", 0, P2_HAND, P1_HAND, None, 1),
    ("steal from p1 tableau", 1, P1_TABLEAU, P2_HAND, None, 1),
    ("grab from p2 board", 0, P2_TABLEAU, P1_HAND, None, 1),

    # Giving to other players
    ("give Ace of Spades to p2", 0, None, P2_HAND, [ACE_OF_SPADES], 1),
    ("pass card to p1", 1, P2_HAND, P1_HAND, None, 1),
    ("give to p2 tableau", 0, P1_HAND, P2_TABLEAU, None, 1),
    
    # Standard draw logic 
    ("draw 3", 0, STACK, P1_HAND, None, 3),
    ("take from discard", 1, DISCARD, P2_HAND, None, 1),
    ("take from pile", 1, DISCARD, P2_HAND, None, 1),
    ("pick A♣ from p3's tableau", 1, P3_TABLEAU, P2_HAND, [ACE_OF_CLUBS], 1),
    ("put three of clubs in p2's hand", 0, None, P2_HAND, [THREE_OF_CLUBS], 1),
    ("draw 4 of diamonds", 0, None, P1_HAND, [FOUR_OF_DIAMONDS], 1),

    # Basic drawing
    ("draw", 0, STACK, P1_HAND, None, 1),
    ("hit", 0, STACK, P1_HAND, None, 1),
    ("take", 1, STACK, P2_HAND, None, 1), 

    # Drawing with counts
    ("draw 3", 0, STACK, P1_HAND, None, 3),
    ("draw 5 cards", 1, STACK, P2_HAND, None, 5),

    ("discard", 1, P2_HAND, DISCARD, None, 1),
    ("discard 1", 0, P1_HAND, DISCARD, None, 1),
    ("dump KH, JD", 2, None, DISCARD, [KING_OF_HEARTS, JACK_OF_DIAMONDS], 2),
    ("trash TD from tableau", 0, P1_TABLEAU, DISCARD, [TEN_OF_DIAMONDS], 1),
    ("dump 3 from my hand", 3, P4_HAND, DISCARD, None, 3),

    # Drawing from discard/pile
    ("take from discard", 0, DISCARD, P1_HAND, None, 1),
    ("get from pile", 1, DISCARD, P2_HAND, None, 1), 
    ("draw 2 from discard", 0, DISCARD, P1_HAND, None, 2),

    # Grabing specifc cards doesn't require a source
    ("get ace of spades", 0, None, P1_HAND, [ACE_OF_SPADES], 1),

    # --- Interactions between players ---
    ("take from p2", 0, P2_HAND, P1_HAND, None, 1),      # P1 steals from P2
    ("give to p1", 1, P2_HAND, P1_HAND, None, 1),      # P2 gives to P1
    ("steal from p1 tableau", 0, P1_TABLEAU, P1_HAND, None, 1), # Oops, P1 steals from self?
    ("grab from p2 tableau", 0, P2_TABLEAU, P1_HAND, None, 1),  # P1 takes from P2's board
    ("pass", 0, P1_HAND, P2_HAND, None, 1),
    ("transfer four of diamonds from p1's Tableau to p3's hand", 2, P1_TABLEAU, P3_HAND, [FOUR_OF_DIAMONDS], 1),
    ("send 4 cards from the stack to p3's hand", 2, STACK, P3_HAND, None, 4),

])
def test_interactions(text, player_idx, expected_source, expected_target, expected_card, expected_count):
    action = interpret_input(text, player_idx)
    
    assert action is not None
    assert action.source == expected_source
    assert action.target == expected_target
    assert action.count == expected_count
    if expected_card:
        assert action.cards == expected_card

# --- Parameterized 'None' / Garbage Tests ---

@pytest.mark.parametrize("text", [
    "Ace of Spades",
    "king of hearts",
    "Get Put Ace of Spades",
    "hello?",
    "",
    "   ",
    "invalid command",
    # "draw nothing", # technically 0 or invalid count might return None depending on regex
])
def test_invalid_input(text):
    """Verify that unrelated or empty text returns None."""
    assert interpret_input(text, 0) is None
