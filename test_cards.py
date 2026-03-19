import pytest

from cards import (
    CardSet,
)
from enums import *
# Import Card, Rank, Suit, and all Enums

# ---------- Enum tests ----------

def test_card_rank_and_suit():
    c = ACE_OF_SPADES
    assert c.rank == ACE
    assert c.suit == SPADES


def test_card_names():
    c = QUEEN_OF_SPADES
    assert c.long_name() == "Queen of Spades"
    assert c.short_name() == "Q♠"
    c = TEN_OF_CLUBS
    assert c.long_name() == "Ten of Clubs"
    assert c.short_name() == "T♣"
    c = ACE_OF_DIAMONDS
    assert c.long_name() == "Ace of Diamonds"
    assert c.short_name() == "A♢"
    c = FOUR_OF_HEARTS
    assert c.long_name() == "Four of Hearts"
    assert c.short_name() == "4♡"


def test_card_ordering():
    assert ACE_OF_CLUBS < TWO_OF_CLUBS
    assert TEN_OF_CLUBS < JACK_OF_CLUBS
    assert KING_OF_CLUBS < ACE_OF_DIAMONDS
    assert KING_OF_DIAMONDS < ACE_OF_HEARTS
    assert KING_OF_HEARTS < ACE_OF_SPADES

# ----------- Card Creation -------------

def test_from_rank_suit_all_suits_ace():
    assert Card.from_rank_suit(Rank.ACE, Suit.CLUBS) == ACE_OF_CLUBS
    assert Card.from_rank_suit(Rank.ACE, Suit.DIAMONDS) == ACE_OF_DIAMONDS
    assert Card.from_rank_suit(Rank.ACE, Suit.HEARTS) == ACE_OF_HEARTS
    assert Card.from_rank_suit(Rank.ACE, Suit.SPADES) == ACE_OF_SPADES


def test_from_rank_suit_round_trip():
    """ Ensure rank/suit properties round-trip correctly.  """
    for card in Card:
        rebuilt = Card.from_rank_suit(card.rank, card.suit)
        assert rebuilt is card


def test_from_rank_suit_identity():
    """ Must return the *existing enum member*, not a new object.  """
    c1 = Card.from_rank_suit(Rank.QUEEN, Suit.HEARTS)
    c2 = Card.QUEEN_OF_HEARTS

    assert c1 is c2


def test_from_rank_suit_invalid_rank_type():
    with pytest.raises(TypeError):
        Card.from_rank_suit(1, Suit.CLUBS)  # type: ignore


def test_from_rank_suit_invalid_suit_type():
    with pytest.raises(TypeError):
        Card.from_rank_suit(Rank.ACE, 0)  # type: ignore

# ---------- CardSet initialization ----------

def test_empty_cardset():
    cs = CardSet()
    assert len(cs) == 0
    assert not cs
    # test creation from empty card set
    cs2 = CardSet(cs)
    assert len(cs2) == 0



def test_standard_deck():
    deck = CardSet.standard_deck()
    assert len(deck) == 52
    assert deck.cards[0] == ACE_OF_CLUBS
    assert deck.cards[-1] == KING_OF_SPADES


# ---------- Add ----------

def test_add_single_card():
    cs = CardSet()
    added = cs.add(ACE_OF_SPADES)

    assert added == [ACE_OF_SPADES]
    assert len(cs) == 1
    assert ACE_OF_SPADES in cs


def test_add_multiple_cards_variadic():
    cs = CardSet()
    cs.add(ACE_OF_SPADES, KING_OF_SPADES)

    assert len(cs) == 2
    assert ACE_OF_SPADES in cs
    assert KING_OF_SPADES in cs


def test_add_multiple_cards_iterable():
    cs = CardSet()
    cs.add([ACE_OF_SPADES, KING_OF_SPADES])

    assert len(cs) == 2


def test_add_rejects_invalid_type():
    cs = CardSet()
    with pytest.raises(TypeError):
        cs.add(123)  # type: ignore

# ---------- Draw ----------

def test_draw_single_card():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    card = cs.draw()

    assert card == ACE_OF_SPADES
    assert len(cs) == 1


def test_draw_multiple_cards():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    cards = cs.draw(2)

    assert cards == [ACE_OF_SPADES, KING_OF_SPADES]
    assert len(cs) == 1
    assert cs.draw() == QUEEN_OF_SPADES


def test_draw_too_many_raises():
    cs = CardSet([ACE_OF_SPADES])
    with pytest.raises(IndexError):
        cs.draw(2)


def test_draw_from_empty_raises():
    cs = CardSet()
    with pytest.raises(IndexError):
        cs.draw()


def test_draw_with_card_raises():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    with pytest.raises(ValueError):
        cs.draw(ACE_OF_SPADES)

# ---------- Pick ----------

def test_pick_single_card_variadic():
    """Verify picking a single card as a positional argument."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    # pick() removes the card from the internal list
    picked = cs.pick(ACE_OF_SPADES)
    
    assert picked == [ACE_OF_SPADES]
    assert len(cs) == 1
    assert ACE_OF_SPADES not in cs.cards

def test_pick_multiple_cards_variadic():
    """Verify picking multiple cards as positional arguments."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    picked = cs.pick(ACE_OF_SPADES, QUEEN_OF_SPADES)
    
    assert picked == [ACE_OF_SPADES, QUEEN_OF_SPADES]
    assert len(cs) == 1
    assert KING_OF_SPADES in cs.cards

def test_pick_multiple_cards_iterable():
    """Verify picking cards passed as a single list or iterable."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    # The method detects the single iterable argument
    picked = cs.pick([KING_OF_SPADES, QUEEN_OF_SPADES])
    
    assert picked == [KING_OF_SPADES, QUEEN_OF_SPADES]
    assert len(cs) == 1

def test_pick_missing_card():
    """Verify that picking a card not in the set returns an empty list without error."""
    cs = CardSet([ACE_OF_SPADES])
    # ValueError is caught internally if the card is missing
    picked = cs.pick(KING_OF_SPADES)
    
    assert picked == []
    assert len(cs) == 1

def test_pick_partial_existence():
    """Verify behavior when picking a mix of existing and non-existing cards."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    picked = cs.pick(ACE_OF_SPADES, ACE_OF_CLUBS)
    
    assert picked == [ACE_OF_SPADES]
    assert len(cs) == 1

def test_pick_duplicate_request():
    """Verify picking the same card twice when only one instance exists."""
    cs = CardSet([ACE_OF_SPADES])
    # Once the first ACE is popped, the second index search fails gracefully
    picked = cs.pick(ACE_OF_SPADES, ACE_OF_SPADES)
    
    assert picked == [ACE_OF_SPADES]
    assert len(cs) == 0

def test_pick_invalid_type_raises():
    """Verify that passing non-Card objects raises a TypeError."""
    cs = CardSet([ACE_OF_SPADES])
    with pytest.raises(TypeError, match="Expected Card"):
        cs.pick("Not A Card")

# ---------- Pull ----------

def test_pull_single_card_random():
    """Verify pulling a single card (n=None) removes it and returns a Card."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    original_count = len(cs)
    
    pulled = cs.pull()
    
    assert isinstance(pulled, Card)
    assert len(cs) == original_count - 1
    assert pulled not in cs.cards

def test_pull_multiple_cards():
    """Verify pulling n cards returns a list and reduces the set size."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES, JACK_OF_SPADES])
    n = 2
    original_count = len(cs)
    
    pulled = cs.pull(n)
    
    assert isinstance(pulled, list)
    assert len(pulled) == n
    assert len(cs) == original_count - n
    for card in pulled:
        assert card not in cs.cards

def test_pull_from_empty_raises():
    """Should raise IndexError when pulling from an empty set."""
    cs = CardSet()
    with pytest.raises(IndexError, match="Empty of cards"):
        cs.pull()

def test_pull_too_many_raises():
    """Should raise IndexError if n is greater than the set size."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    with pytest.raises(IndexError, match="Not enough cards to pull"):
        cs.pull(3)

def test_pull_zero_cards():
    """Verify that pulling 0 cards returns an empty list and changes nothing."""
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    pulled = cs.pull(0)
    
    assert pulled == []
    assert len(cs) == 2


# ------ Stack vs Queue -------

def test_add_queue():
    cs = CardSet(stack = False)
    cs.add(ACE_OF_SPADES)
    assert cs.cards == [ACE_OF_SPADES]

    cs.add(TWO_OF_CLUBS)
    assert cs.cards == [ ACE_OF_SPADES, TWO_OF_CLUBS]

    assert cs.draw() == ACE_OF_SPADES
    assert cs.cards == [TWO_OF_CLUBS]

    assert cs.draw() == TWO_OF_CLUBS
    assert cs.cards == []

def test_add_stack():
    cs = CardSet(stack = True)
    cs.add(ACE_OF_SPADES)
    assert cs.cards == [ACE_OF_SPADES]

    cs.add(TWO_OF_CLUBS)
    assert cs.cards == [TWO_OF_CLUBS, ACE_OF_SPADES]

    assert cs.draw() == TWO_OF_CLUBS
    assert cs.cards == [ACE_OF_SPADES]

    assert cs.draw() == ACE_OF_SPADES
    assert cs.cards == []


# ---------- Slicing ----------

def test_slicing_returns_cardset():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES])
    sub = cs[:2]

    assert isinstance(sub, CardSet)
    assert len(sub) == 2
    assert sub.cards == [ACE_OF_SPADES, KING_OF_SPADES]


def test_indexing_returns_card():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    assert cs[0] == ACE_OF_SPADES


# ---------- Sorting ----------

def test_sort_by_rank():
    cs = CardSet([KING_OF_SPADES, ACE_OF_SPADES, QUEEN_OF_SPADES])
    cs.sort_by_rank()

    assert cs.cards == [ACE_OF_SPADES, QUEEN_OF_SPADES, KING_OF_SPADES]


def test_sort_by_suit():
    cs = CardSet([ACE_OF_SPADES, TWO_OF_CLUBS, THREE_OF_CLUBS])
    cs.sort_by_suit()

    assert cs.cards == [TWO_OF_CLUBS, THREE_OF_CLUBS, ACE_OF_SPADES]


# ---------- Shuffle ----------

def test_shuffle_preserves_cards():
    cs = CardSet.standard_deck()
    before = set(cs.cards)

    cs.shuffle()

    after = set(cs.cards)
    assert before == after
    assert len(cs) == 52


# ---------- Membership ----------

def test_membership():
    cs = CardSet([ACE_OF_SPADES])
    assert ACE_OF_SPADES in cs
    assert KING_OF_SPADES not in cs


# ---------- Pretty printing ----------

def test_format_long():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    s = cs.format("long")

    assert s == "Ace of Spades, King of Spades"


def test_format_short():
    cs = CardSet([ACE_OF_SPADES, KING_OF_SPADES])
    s = cs.format("short")

    assert s == "A♠ K♠"


def test_str_and_repr():
    cs = CardSet([ACE_OF_SPADES])
    assert str(cs) == "A♠"
    assert "CardSet(A♠)" in repr(cs)
