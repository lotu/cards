import pytest
from gameserver import  interpret_input
from enums import *

# --- Test Parsing of Complex Interactions ---

test_parameters = [
    # Playing to own tableau
    ("play Ace of Spades", PLAYER_1, None, P1_TABLEAU, [ACE_OF_SPADES], 1),
    ("put King of Hearts on table", PLAYER_2, None, P2_TABLEAU, [KING_OF_HEARTS], 1),

    # Taking from other players
    ("take from p2", PLAYER_1, P2_HAND, P1_HAND, None, 1),
    ("steal from p1 tableau", PLAYER_2, P1_TABLEAU, P2_HAND, None, 1),
    ("grab from p2 board", PLAYER_1, P2_TABLEAU, P1_HAND, None, 1),

    # Giving to other players
    ("give Ace of Spades to p2", PLAYER_1, None, P2_HAND, [ACE_OF_SPADES], 1),
    ("send card to p1", PLAYER_2, P2_HAND, P1_HAND, None, 1),
    ("give to p2 tableau", PLAYER_1, P1_HAND, P2_TABLEAU, None, 1),
    
    # Standard draw logic 
    ("draw 3", PLAYER_1, STACK, P1_HAND, None, 3),
    ("take from discard", PLAYER_2, DISCARD, P2_HAND, None, 1),
    ("take from pile", PLAYER_2, DISCARD, P2_HAND, None, 1),
    ("pick A♣ from p3's tableau", PLAYER_2, P3_TABLEAU, P2_HAND, [ACE_OF_CLUBS], 1),
    ("put three of clubs in p2's hand", PLAYER_1, None, P2_HAND, [THREE_OF_CLUBS], 1),
    ("draw 4 of diamonds", PLAYER_1, None, P1_HAND, [FOUR_OF_DIAMONDS], 1),

    # Basic drawing
    ("draw", PLAYER_1, STACK, P1_HAND, None, 1),
    ("hit", PLAYER_1, STACK, P1_HAND, None, 1),
    ("take", PLAYER_2, STACK, P2_HAND, None, 1), 

    # Drawing with counts
    ("draw 3", PLAYER_1, STACK, P1_HAND, None, 3),
    ("draw 5 cards", PLAYER_2, STACK, P2_HAND, None, 5),

    ("discard", PLAYER_2, P2_HAND, DISCARD, None, 1),
    ("discard 1", PLAYER_1, P1_HAND, DISCARD, None, 1),
    ("trash TD from tableau", PLAYER_1, P1_TABLEAU, DISCARD, [TEN_OF_DIAMONDS], 1),
    ("dump 3 from my hand", PLAYER_4, P4_HAND, DISCARD, None, 3),
    # XXX Questionable choice discard defaults to anywhere if no source is specified
    # Not sure if that is the correct behavior
    ("dump KH, JD", PLAYER_3, None, DISCARD, [KING_OF_HEARTS, JACK_OF_DIAMONDS], 2),
    ("discard 2 of hears and 6 of hearts", PLAYER_2, None, DISCARD, [SIX_OF_HEARTS], 1),  

    # Drawing from discard/pile
    ("take from discard", PLAYER_1, DISCARD, P1_HAND, None, 1),
    ("get from pile", PLAYER_2, DISCARD, P2_HAND, None, 1), 
    ("draw 2 from discard", PLAYER_1, DISCARD, P1_HAND, None, 2),

    # Grabing specifc cards doesn't require a source
    ("get ace of spades", PLAYER_1, None, P1_HAND, [ACE_OF_SPADES], 1),

    # --- Interactions between players ---
    ("take from p2", PLAYER_1, P2_HAND, P1_HAND, None, 1),      # P1 steals from P2
    ("give to p1", PLAYER_2, P2_HAND, P1_HAND, None, 1),      # P2 gives to P1
    ("steal from p1 tableau", PLAYER_1, P1_TABLEAU, P1_HAND, None, 1), # Oops, P1 steals from self?
    ("grab from p2 tableau", PLAYER_1, P2_TABLEAU, P1_HAND, None, 1),  # P1 takes from P2's board
    ("transfer four of diamonds from p1's Tableau to p3's hand", PLAYER_3, P1_TABLEAU, P3_HAND, [FOUR_OF_DIAMONDS], 1),
    ("send 4 cards from the stack to p3's hand", PLAYER_3, STACK, P3_HAND, None, 4),
]
@pytest.mark.parametrize("text, player_idx, expected_source, expected_target, expected_card, expected_count", test_parameters)
def test_interactions(text, player_idx, expected_source, expected_target, expected_card, expected_count):
    action = interpret_input(text, player_idx)
    
    assert action is not None
    assert action.source == expected_source
    assert action.target == expected_target
    assert action.count == expected_count
    if expected_card:
        assert action.cards == expected_card

# --- Parameterized 'None' / Garbage Tests ---

test_parameters = [
    "Ace of Spades",
    "king of hearts",
    "Get Put Ace of Spades",
    "hello?",
    "pass",
    "give",
    "",
    "   ",
    "invalid command",
    # "draw nothing", # technically 0 or invalid count might return None depending on regex
]
@pytest.mark.parametrize("text", test_parameters)
def test_invalid_input(text):
    """Verify that unrelated or empty text returns None."""
    assert interpret_input(text, PLAYER_1) is None
