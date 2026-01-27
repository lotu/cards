import pytest

from cards import (
    CardSet,
    Card,
    Rank,
    Suit,
    ACE_OF_SPADES,
    KING_OF_SPADES,
    QUEEN_OF_SPADES,
    TWO_OF_CLUBS,
    THREE_OF_CLUBS,
)


# ---------- Enum tests ----------

def test_card_rank_and_suit():
    c = ACE_OF_SPADES
    assert c.rank == Rank.ACE
    assert c.suit == Suit.SPADES


def test_card_names():
    c = QUEEN_OF_SPADES
    assert c.long_name() == "Queen of Spades"
    assert c.short_name() == "Q♠"


def test_card_ordering():
    assert Card.ACE_OF_CLUBS < Card.KING_OF_CLUBS
    assert Card.KING_OF_CLUBS < Card.ACE_OF_DIAMONDS


# ---------- CardSet initialization ----------

def test_empty_cardset():
    cs = CardSet()
    assert len(cs) == 0
    assert not cs


def test_standard_deck():
    deck = CardSet.standard_deck()
    assert len(deck) == 52
    assert deck.cards[0] == Card.ACE_OF_CLUBS
    assert deck.cards[-1] == Card.KING_OF_SPADES


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
    assert str(cs) == "Ace of Spades"
    assert "A♠" in repr(cs)
