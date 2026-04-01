import pytest
from copy import deepcopy
from enums import *
from cards import *
from parse import parse_card_set
from logging import *

# --------------- Locate Card -------------
def test_location_has_cards_basic():
    """Verify checking for cards in specific locations."""
    table = Table(empty=True)
    table.seats[0].hand.add(ACE_OF_SPADES, KING_OF_SPADES)
    table.stack.add(TWO_OF_CLUBS)
    
    # Check single card
    assert location_has_cards(table, P1_HAND, ACE_OF_SPADES) is True
    assert location_has_cards(table, P1_HAND, ACE_OF_CLUBS) is False
    
    # Check multiple cards
    assert location_has_cards(table, P1_HAND, [ACE_OF_SPADES, KING_OF_SPADES]) is True
    
    # Check central piles
    assert location_has_cards(table, STACK, TWO_OF_CLUBS) is True

def test_location_has_cards_quantities():
    """Verify that the check respects card quantities (multiset logic)."""
    table = Table(empty=True)
    table.discard.add(ACE_OF_SPADES)
    
    # Should be False because there is only one Ace of Spades in the pile
    assert location_has_cards(table, DISCARD, [ACE_OF_SPADES, ACE_OF_SPADES]) is False

def test_locate_card_success():
    """Verify that a card can be found anywhere on the table."""
    table = Table(empty=True)
    table.seats[2].tableau.add(QUEEN_OF_HEARTS) # P3 Tableau
    table.discard.add(JACK_OF_DIAMONDS)
    
    assert locate_card(table, QUEEN_OF_HEARTS) == P3_TABLEAU
    assert locate_card(table, JACK_OF_DIAMONDS) == DISCARD

def test_locate_card_missing_and_invalid():
    """Verify behavior when a card is not present or input is invalid."""
    table = Table(empty=True)
    
    # Not on table
    assert locate_card(table, ACE_OF_CLUBS) is None
    
    # Invalid type
    with pytest.raises(TypeError):
        locate_card(table, "Ace of Spades") # type: ignore

# ---------- Locate Cards (Plural) ----------

def test_locate_cards_success():
    """Verify finding a group of cards in a single location."""
    table = Table(empty=True)
    my_cards = [ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES]
    table.seats[0].hand.add(my_cards)

    assert locate_cards(table, my_cards) == P1_HAND

def test_locate_cards_fails_when_split():
    """Verify that it returns None if cards are spread across different locations."""
    table = Table(empty=True)
    table.seats[0].hand.add(ACE_OF_SPADES)
    table.seats[1].hand.add(KING_OF_SPADES)

    # Even though both cards exist on the table, they aren't in ONE location
    assert locate_cards(table, [ACE_OF_SPADES, KING_OF_SPADES]) is None

def test_locate_cards_fails_when_missing_one():
    """Verify failure if even one card in the set is missing from the location."""
    table = Table(empty=True)
    table.seats[0].hand.add(ACE_OF_SPADES)

    assert locate_cards(table, [ACE_OF_SPADES, KING_OF_SPADES]) is None

def test_locate_cards_ambiguity_failure():
    """Verify failure if the set of cards could be found in multiple locations."""
    table = Table(empty=True)
    # Put an Ace of Spades in two different places
    table.seats[0].hand.add(ACE_OF_SPADES)
    table.seats[1].hand.add(ACE_OF_SPADES)

    # It shouldn't guess which one you want
    assert locate_cards(table, [ACE_OF_SPADES]) is None

def test_locate_cards_respects_quantity():
    """Verify it fails if the location has the card, but not enough of them."""
    table = Table(empty=True)
    table.seats[0].hand.add(ACE_OF_SPADES)

    # Asking for two, but only one is there
    assert locate_cards(table, [ACE_OF_SPADES, ACE_OF_SPADES]) is None

def test_locate_cards_respects_quantity_succuss():
    """Verify it fails if the location has the card, but not enough of them."""
    table = Table(empty=True)
    table.seats[0].hand.add(ACE_OF_SPADES, KING_OF_DIAMONDS, ACE_OF_SPADES)

    # Asking for two, but only one is there
    assert locate_cards(table, [ACE_OF_SPADES, ACE_OF_SPADES]) == P1_HAND

def test_locate_cards_success():
    """Verify finding a group of cards in a single location."""
    table = Table(seats=3, empty=True)
    my_cards = [ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES]
    table.seats[0].hand.add(my_cards)

    assert locate_cards(table, my_cards) == P1_HAND



# --------- Seat Sees Cards ---------------
def test_seat_sees_cards_visibility_rules():
    """Verify strict visibility rules for players."""
    t = Table(empty=True)
    t.seats[0].hand.add(ACE_OF_SPADES)    # P1 Hand
    t.seats[1].hand.add(KING_OF_SPADES)   # P2 Hand
    t.seats[1].tableau.add(QUEEN_OF_HEARTS) # P2 Tableau
    t.discard.add(JACK_OF_DIAMONDS)      # Discard
    t.stack.add(TWO_OF_CLUBS)            # Stack

    # Player 1 (seat_index 0)
    assert seat_sees_cards(t, 0, [ACE_OF_SPADES]) is True    # Own hand
    assert seat_sees_cards(t, 0, [QUEEN_OF_HEARTS]) is True  # Opponent Tableau
    assert seat_sees_cards(t, 0, [JACK_OF_DIAMONDS]) is True # Discard

    assert seat_sees_cards(t, 0, [KING_OF_SPADES]) is False  # Opponent Hand
    assert seat_sees_cards(t, 0, [TWO_OF_CLUBS]) is False    # Stack

# --------- Execute CardMove ----------------


@pytest.mark.parametrize("card_move, setup_cards, moved_cards, expected_source_len, target_cards", [
    # Scenario 1: Player 1 plays a card from hand to their own tableau
    (
        CardMove(source=P1_HAND, target=P1_TABLEAU, cards=ACE_OF_SPADES),
        {P1_HAND: [ACE_OF_SPADES], P1_TABLEAU: [TWO_OF_SPADES]},
        [ACE_OF_SPADES],
        0, [TWO_OF_SPADES, ACE_OF_SPADES] 
    ),
    # Move with card set not properlly done XXX
    # # Scenario 1: Player 1 plays a card from hand to their own tableau
    # (
    #     CardMove(source=P1_HAND, target=P1_TABLEAU, cards=[ACE_OF_SPADES]),
    #     {P1_HAND: [ACE_OF_SPADES], P1_TABLEAU: []},
    #     0, 1
    # ),

    # # Scenario 2: Player 1 takes 1 random card from Player 2's hand
    (
        CardMove(source=P2_HAND, target=P1_HAND, count=1),
        {P2_HAND: [KING_OF_CLUBS, QUEEN_OF_CLUBS], P1_HAND: [TWO_OF_HEARTS]},
        [KING_OF_CLUBS],
        1, [TWO_OF_HEARTS, KING_OF_CLUBS] 
    ),
    
    # Player takes cards from stack
    (
        CardMove(source=STACK, target=P1_HAND, count=2),
        {STACK: [KING_OF_CLUBS, QUEEN_OF_CLUBS, JACK_OF_CLUBS], P1_HAND: []},
        [KING_OF_CLUBS, QUEEN_OF_CLUBS],
        1, [KING_OF_CLUBS, QUEEN_OF_CLUBS],
    ),

    # Player takes cards from discard
    (
        CardMove(source=DISCARD, target=P1_HAND, count=2),
        {DISCARD: [KING_OF_CLUBS, QUEEN_OF_CLUBS, JACK_OF_CLUBS], P1_HAND: []},
        [KING_OF_CLUBS, QUEEN_OF_CLUBS],
        1, [KING_OF_CLUBS, QUEEN_OF_CLUBS],
    ),

    # Player discards note ordering of target
    (
        CardMove(source=P1_HAND, target=DISCARD, count=2),
        {P1_HAND: [KING_OF_CLUBS, QUEEN_OF_CLUBS, JACK_OF_CLUBS], DISCARD: [THREE_OF_HEARTS]},
        [KING_OF_CLUBS, QUEEN_OF_CLUBS],
        1, [KING_OF_CLUBS, QUEEN_OF_CLUBS, THREE_OF_HEARTS],
    ),
    # Scenario 3: Player 1 steals a specific card from Player 2's tableau
    (
        CardMove(source=P2_TABLEAU, target=P1_HAND, cards=TEN_OF_DIAMONDS),
        {P2_TABLEAU: [TEN_OF_DIAMONDS, ACE_OF_SPADES], P1_HAND: []},
        [TEN_OF_DIAMONDS],
        1, [TEN_OF_DIAMONDS]
    ),
])
def test_execute_player_moves_old(table, card_move, setup_cards, moved_cards, expected_source_len, target_cards):
    """Verify Table.execute_card_move correctly moves cards between player zones."""
    # 1. Setup the state
    for loc, card_list in setup_cards.items():
        # Using the helper you wrote for the Table class
        cardset = table._get_cardset(loc)
        cardset.cards = list(card_list)

    # 2. Execute
    assert moved_cards == table.execute_card_move(card_move)

    # 3. Verify
    assert len(table._get_cardset(card_move.source).cards) == expected_source_len
    assert target_cards == table._get_cardset(card_move.target).cards

    # If a specific card was moved, verify it's in the target
    if card_move.cards:
        assert card_move.cards in table._get_cardset(card_move.target).cards

@pytest.fixture
def table():
    """Provides a clean Table for testing."""
    t =  Table(seats=4, empty=True)
    t.stack.add(parse_card_set("A♠ 2♠ 3♠ 4♠ 5♠ 6♠ 7♠ 8♠ 9♠ T♠")) 
    t.discard.add(parse_card_set("A♢ 2♢ 3♢ 4♢ 5♢ 6♢ 7♢ 8♢ 9♢ T♢")) 
    t.seats[0].hand.add(parse_card_set("A♡ 2♡ 3♡ 4♡ 5♡ 6♡ 7♡ 8♡ 9♡ T♡"))
    t.seats[1].hand.add(parse_card_set("A♣ 2♣ 3♣ 4♣ 5♣ 6♣ 7♣ 8♣ 9♣ T♣"))
    t.seats[1].tableau.add(parse_card_set("K♠ K♡ K♣ K♢")) 
    t.seats[2].tableau.add(parse_card_set("Q♠ Q♡ Q♣ Q♢")) 
    t.seats[2].hand.add(parse_card_set("J♠ J♡ J♣ J♢")) 
    return t

@pytest.mark.parametrize(
    "cards, count, source, target, expected, not_expected",
    [
        # 1 Play specific card from P1 hand to P1 tableau
        (ACE_OF_HEARTS, 1, P1_HAND, P1_TABLEAU,
         {P1_TABLEAU: [ACE_OF_HEARTS]}, {P1_HAND: [ACE_OF_HEARTS]}
        ),
        # Draw 2 Cards
        (None, 2, STACK, P4_HAND,
         {P4_HAND: [ACE_OF_SPADES, TWO_OF_SPADES]}, {STACK: [ACE_OF_SPADES, TWO_OF_SPADES]}
        ),
        # Draw 2 Cards
        (None, 2, DISCARD, P4_HAND,
         {P4_HAND: [ACE_OF_DIAMONDS, TWO_OF_DIAMONDS]}, {STACK: [ACE_OF_DIAMONDS, TWO_OF_DIAMONDS]}
        ),
        # Get specific card from discard
        (TWO_OF_DIAMONDS, 1, DISCARD, P4_HAND,
         {P4_HAND: [TWO_OF_DIAMONDS]}, {STACK: [TWO_OF_DIAMONDS]}
        ),
        # Get specific card form discard without naming
        (THREE_OF_DIAMONDS, 1, None, P4_HAND,
         {P4_HAND: [THREE_OF_DIAMONDS]}, {STACK: [THREE_OF_DIAMONDS]}
        ),
        # Play a specific card
        (TEN_OF_HEARTS, 1, P1_HAND, P1_TABLEAU,
         {P1_TABLEAU: [TEN_OF_HEARTS]}, {P1_HAND: [TEN_OF_HEARTS]}
        ),
    ],
)
def test_execute_player_moves(table, source, target, cards, count, expected, not_expected):
    """Verify execute_card_move moves exact card contents correctly."""
    # ---- Execute ----
    # assert isinstance(cards, Card)
    assert table.execute_card_move(CardMove(source, target, count, cards))
    debug(f"table:\n{table.__str__()}")

        
    # ---- Verify exact contents ----
    for loc, expected_cards in expected.items():
        actual_cards = table._get_cardset(loc).cards
        for card in expected_cards:
            assert card in actual_cards
        
    for loc, not_expected_cards in not_expected.items():
        actual_cards = table._get_cardset(loc).cards
        for card in not_expected_cards:
            assert card not in actual_cards


@pytest.mark.parametrize(
    "cards, count, source, target",
    [
        ( None, 11, P1_HAND, P1_TABLEAU),
        ( None, 1, P4_TABLEAU, P4_HAND),
        ( JACK_OF_DIAMONDS, 1, DISCARD, P4_HAND),
        ( [ACE_OF_SPADES, ACE_OF_CLUBS], 2, None, P4_HAND),
    ],
)
def test_execute_failure(table, source, target, cards, count):
    """Verify execute_card_move moves exact card contents correctly."""
    # ---- Execute ----
    before_table = deepcopy(table)
    assert not table.execute_card_move(CardMove(source, target, count, cards))
        
    assert before_table == table
