import pytest
from parse import *
from enums import *


ACTION_TEST_CASES = [
    # (Input Text, Actor, Expected Intent Type, Expected Attributes)
    ("!Hello everyone", PLAYER_1, Say, {"text": "Hello everyone", "target": None}),
    ("!p2 I have the ace", PLAYER_1, Say, {"text": "I have the ace", "target": PLAYER_2}),
    # ("shuffle hand", PLAYER_1, Reorder, {"target": P1_HAND}),
    ("draw 1", PLAYER_2, CardMove, {"source": STACK, "target": P2_HAND, "count": 1}),
]

@pytest.mark.parametrize("text, actor, intent_type, expected", ACTION_TEST_CASES)
def test_input_interpretation(text, actor, intent_type, expected):
    action = parse_action(text, actor)
    
    assert action is not None
    assert isinstance(action.intent, intent_type)
    
    # Check attributes of the intent
    for key, value in expected.items():
        assert getattr(action.intent, key) == value

# --- Test Parsing of Complex Intercard_moves ---

test_parameters = [
    # Playing to own tableau
    ("play Ace of Spades", PLAYER_1, None, P1_TABLEAU, [ACE_OF_SPADES], 1),
    ("put King of Hearts on table", PLAYER_2, None, P2_TABLEAU, [KING_OF_HEARTS], 1),

    # Taking from other players
    ("take from p2", PLAYER_1, P2_HAND, P1_HAND, None, 1),
    ("steal from p1 tableau", PLAYER_2, P1_TABLEAU, P2_HAND, None, 1),
    ("grab from p2 board", PLAYER_1, P2_TABLEAU, P1_HAND, None, 1),

    # Using full name of player
    ("take from Player 2", PLAYER_1, P2_HAND, P1_HAND, None, 1),
    ("steal from Player 1's tableau", PLAYER_2, P1_TABLEAU, P2_HAND, None, 1),
    ("take from player 2", PLAYER_1, P2_HAND, P1_HAND, None, 1),
    ("give Ace of Spades to player 2", PLAYER_1, None, P2_HAND, [ACE_OF_SPADES], 1),
    ("Give player 1 K♡ K♠", PLAYER_2, None, P1_HAND, [KING_OF_HEARTS, KING_OF_SPADES], 2),

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

    # --- Intercard_moves between players ---
    ("take from p2", PLAYER_1, P2_HAND, P1_HAND, None, 1),      # P1 steals from P2
    ("give to p1", PLAYER_2, P2_HAND, P1_HAND, None, 1),      # P2 gives to P1
    ("steal from p1 tableau", PLAYER_1, P1_TABLEAU, P1_HAND, None, 1), # Oops, P1 steals from self?
    ("grab from p2 tableau", PLAYER_1, P2_TABLEAU, P1_HAND, None, 1),  # P1 takes from P2's board
    ("transfer four of diamonds from p1's Tableau to p3's hand", PLAYER_3, P1_TABLEAU, P3_HAND, [FOUR_OF_DIAMONDS], 1),
    ("send 4 cards from the stack to p3's hand", PLAYER_3, STACK, P3_HAND, None, 4),
]
@pytest.mark.parametrize("text, player_idx, expected_source, expected_target, expected_card, expected_count", test_parameters)
def test_card_moves(text, player_idx, expected_source, expected_target, expected_card, expected_count):
    card_move = parse_card_move(text, player_idx)
    
    assert card_move is not None
    assert card_move.source == expected_source
    assert card_move.target == expected_target
    assert card_move.count == expected_count
    if expected_card:
        assert card_move.cards == expected_card

@pytest.mark.parametrize("text, player_idx, expected_source, expected_target, expected_card, expected_count", test_parameters)
def test_card_moves_actions(text, player_idx, expected_source, expected_target, expected_card, expected_count):
    action = parse_action(text, player_idx)
    
    assert action.player == player_idx
    assert isinstance(action.intent, CardMove)
    card_move = action.intent
    assert card_move is not None
    assert card_move.source == expected_source
    assert card_move.target == expected_target
    assert card_move.count == expected_count
    if expected_card:
        assert card_move.cards == expected_card


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
    assert parse_card_move(text, PLAYER_1) is None

TEST_NAME_MAP = {
    "Joe": PLAYER_1,
    "Alice": PLAYER_2,
    "Bob": PLAYER_3,
    "Charlie": PLAYER_4,
    "Big Al": PLAYER_2  # Multiple names can map to one ID
}

# (Input Text, Actor, Expected Text, Expected Target)
SAY_TEST_PARAMETERS = [
    # --- Global Verbs (Always None target) ---
    ("say Joe is winning", PLAYER_3, "Joe is winning", None),
    ("chat p2 check this out", PLAYER_1, "p2 check this out", None),
    ("say hello everyone", PLAYER_1, "hello everyone", None),
    ("chat Good luck!", PLAYER_2, "Good luck!", None),
    ("!GG", PLAYER_3, "GG", None),
    ("  say   extra spaces  ", PLAYER_4, "extra spaces", None),

    # --- Targeted Verbs (Resolve via p1/player 1) ---
    ("tell p1 hello", PLAYER_2, "hello", PLAYER_1),
    ("tell p2 your turn", PLAYER_1, "your turn", PLAYER_2),
    ("whisper player 4 look here", PLAYER_1, "look here", PLAYER_4),
    ("tell p4", PLAYER_1, "", PLAYER_4),
    ("whisper p3 I have a King", PLAYER_4, "I have a King", PLAYER_3),
    ("!p1 check the stack", PLAYER_2, "check the stack", PLAYER_1),

    # --- Targeted Verbs (Resolve via Name Map) ---
    ("tell Joe check your hand", PLAYER_2, "check your hand", PLAYER_1),
    ("whisper Big Al I have an Ace", PLAYER_3, "I have an Ace", PLAYER_2),
    ("tell Alice", PLAYER_1, "", PLAYER_2),

    # --- Shorthand "!" logic ---
    ("!Joe hi", PLAYER_3, "hi", PLAYER_1),
    ("!p3 check the board", PLAYER_1, "check the board", PLAYER_3),
    ("!No target here", PLAYER_1, "No target here", None),

    # --- Player Id word boundry ---
    ("tell p4 ", PLAYER_1, "", PLAYER_4),
    ("tell p4", PLAYER_1, "", PLAYER_4), 
    ("tell p4 foobar", PLAYER_1, "foobar", PLAYER_4),

    # --- Mixed Casing ---
    ("SAY Hello", PLAYER_1, "Hello", None),
    ("!P2 Hi", PLAYER_3, "Hi", PLAYER_2),
    ("Whisper p1 secret", PLAYER_2, "secret", PLAYER_1),

    # --- Edge Cases ---
    # XXX These are probally not correct
    # XXX TODO reenable ("say p2 is winning", PLAYER_1, "p2 is winning", None), # "p2" is part of message
    ("tell p2 p3 is cheating", PLAYER_1, "p3 is cheating", PLAYER_2),
    ("tell Joelle hi", PLAYER_1, "Joelle hi", None), # Should not match "Joe"
    ("say tell p1 hello", PLAYER_2, "tell p1 hello", None), # 'say' wins, everything else is msg

    # --- Negative Cases (Should return None) ---
    ("draw 2 cards", PLAYER_1, None, None),
    ("play ACE_OF_SPADES", PLAYER_2, None, None),
    ("discard", PLAYER_3, None, None),
    ("pass", PLAYER_4, None, None),
    ("", PLAYER_1, None, None),
    ("   ", PLAYER_2, None, None),
]

@pytest.mark.parametrize("text, actor, expected_text, expected_target", SAY_TEST_PARAMETERS)
def test_parse_say(text, actor, expected_text, expected_target):
    result = parse_say(text, actor, TEST_NAME_MAP)

    if expected_text is None:
        assert result is None
    else:
        assert isinstance(result, Say)
        assert result.text == expected_text
        assert result.target == expected_target 

###############################
# Name identification
#

# Define a problematic name map
RESOLVE_NAME_MAP = {
    "Al": PLAYER_1,
    "Big Al": PLAYER_2,
    "Joe": PLAYER_3,
    "Jo": PLAYER_4,     # "Jo" is a prefix of "Joe"
    "C3PO": PLAYER_1,   # Alphanumeric
    "Dr. Jones": PLAYER_2,
    "p2": PLAYER_4,           # Trap: Name is 'p2' but he's Player 4
    "player 3": PLAYER_1,     # Trap: Name is 'player 3' but he's Player 1
}


RESOLVE_AGGRESSIVE_PARAMETERS = [
    # --- Priority & Shadowing ---
    ("Big Al hello", PLAYER_2, "hello"),         # Longest match wins (Big Al over Al)
    ("Joe, check this", PLAYER_3, "check this"), # "Joe" is found even with comma
    ("Jo is my name", PLAYER_4, "is my name"),   # "Jo" matches exactly
    ("Joelle", None, "Joelle"),                  # "Joe" should NOT match prefix of Joelle

    # --- Hardcoded Shorthand vs Names ---
    ("p1", PLAYER_1, ""),                       # Base case
    ("player   2", PLAYER_2, ""),               # Extra spacing
    ("p3Joe", None , "p3Joe"),                  # This matches "p3" first, leaves "Joe"

    # --- Case Sensitivity & Spacing ---
    ("  bIg al  is here", PLAYER_2, "is here"),  # Case insensitive, leading space
    ("AL: help", PLAYER_1, "help"),              # Punctuation separator ':'
    ("Dr. Jones-message", PLAYER_2, "message"),  # Dash separator '-'

    # --- Alphanumeric Boundaries ---
    ("C3PO check", PLAYER_1, "check"),           # Mixed chars
    ("C3PO4", None, "C3PO4"),                    # Should not match C3PO (4 is alnum)

    # --- Overlapping with Verbs ---
    ("Joe say hello", PLAYER_3, "say hello"),    # If name is before the message
    ("Alice", None, "Alice"),                    # Not in map

    # --- The "P1 Trap" (Shorthand Priority) ---
    # Even though "p2" maps to PLAYER_4 in the name_map,
    # the shorthand check should catch it first and return PLAYER_2 (Seat 2).
    ("p2 hello", PLAYER_2, "hello"),
    ("player 3 stay", PLAYER_3, "stay"), # Should resolve to Seat 3, not PLAYER_1

    # --- Typo/Strictness Check ---
    ("p3Joe", None, "p3Joe"),            # Fails due to \b (No boundary between 3 and J)
    ("p5 hello", None, "p5 hello"),      # Out of range 1-4
    ("p12", None, "p12"),                # Out of range 1-4

    # --- Punctuation & Separators ---
    ("Joe: ready", PLAYER_3, "ready"),
    ("Al-message", PLAYER_1, "message"),
    ("Big Al, wait", PLAYER_2, "wait"),

    # --- Formatting Chaos ---
    ("   p1   ", PLAYER_1, ""),             # Extreme whitespace
    ("PLAYER 1!!!", PLAYER_1, "!!!"),       # Case and punctuation
    ("\ntell p1", None, "\ntell p1"),       # Newlines (should fail resolve_player_id)
    ("", None, ""),                         # Empty
    ("   ", None, "   "),                   # Just spaces
    ("Someone Else", None, "Someone Else"), # Not in map
    ("p12", None, "p12"),                   # Out of range (regex allows 1-4)
]


@pytest.mark.parametrize("text, expected_id, expected_remaining", RESOLVE_AGGRESSIVE_PARAMETERS)
def test_resolve_player_id_aggressive(text, expected_id, expected_remaining):
    player_id, remaining = resolve_player_id(text, RESOLVE_NAME_MAP)

    assert player_id == expected_id
    assert remaining == expected_remaining

# --- Verification of "Physical Table" edge case ---

def test_p1_shorthand_priority():
    """Verify that 'p1' shorthand beats a user named 'p1'."""
    # User maps 'p1' to PLAYER_4
    malicious_map = {"p1": PLAYER_4}
    # But hardcoding should resolve p1 to PLAYER_1
    player_id, _ = resolve_player_id("p1 hello", malicious_map)
    assert player_id == PLAYER_1
