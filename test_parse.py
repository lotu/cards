

import pytest

from enums import *
from parse import *

@pytest.mark.parametrize(
    "text, expected",
    [
        # ---- Ace of Spades ----
        ("ACE_OF_SPADES", ACE_OF_SPADES),
        ("Ace of Spades", ACE_OF_SPADES),
        ("ace of spades", ACE_OF_SPADES),
        ("  Ace   of   Spades  ", ACE_OF_SPADES),
        ("Ace---Spades", ACE_OF_SPADES),
        ("\tace-spade", ACE_OF_SPADES),
        ("Ace-of-of-Spades",ACE_OF_SPADES),
        ("AceOfSpades",ACE_OF_SPADES),
        ("Ace♠",ACE_OF_SPADES),
        ("  A♠", ACE_OF_SPADES),
        ("AS", ACE_OF_SPADES),
        ("A S", ACE_OF_SPADES),
        ("a♠", ACE_OF_SPADES),
        ("A of ♠",ACE_OF_SPADES),

        # ---- Queen of Hearts ----
        ("QUEEN_OF_HEARTS", QUEEN_OF_HEARTS),
        ("Queen of Hearts    ", QUEEN_OF_HEARTS),
        ("queen\n hearts", QUEEN_OF_HEARTS),
        ("queen_of_hearts", QUEEN_OF_HEARTS),
        ("queen-hearts", QUEEN_OF_HEARTS),
        ("qUeEn hEaRtS", QUEEN_OF_HEARTS),
        ("QH", QUEEN_OF_HEARTS),
        ("Q♥", QUEEN_OF_HEARTS),
        ("q♥", QUEEN_OF_HEARTS),

        # ---- Ten of Diamonds ----
        ("TEN_OF_DIAMONDS", TEN_OF_DIAMONDS),
        ("Ten of Diamonds\n", TEN_OF_DIAMONDS),
        ("10_of-diamonds", TEN_OF_DIAMONDS),
        ("Ten Diamonds", TEN_OF_DIAMONDS),
        ("\n\t10 Diamonds", TEN_OF_DIAMONDS),
        ("10D", TEN_OF_DIAMONDS),
        ("10♦", TEN_OF_DIAMONDS),
        ("Td", TEN_OF_DIAMONDS),
        ("T♦", TEN_OF_DIAMONDS),

        # ---- Two of Clubs ----
        ("TWO_OF_CLUBS", TWO_OF_CLUBS),
        ("Two of Clubs", TWO_OF_CLUBS),
        ("2 of clubs", TWO_OF_CLUBS),
        ("2C", TWO_OF_CLUBS),
        ("2♣", TWO_OF_CLUBS),

        # ---- Other Cards ----
        ("Seven Hearts", SEVEN_OF_HEARTS),
        ("7H", SEVEN_OF_HEARTS),
        ("7♥", SEVEN_OF_HEARTS),

        ("King of Diamonds", KING_OF_DIAMONDS),
        ("KD", KING_OF_DIAMONDS),

        ("9S", NINE_OF_SPADES),
        ("9♠", NINE_OF_SPADES),

        ("JC", JACK_OF_CLUBS),
        ("J♣", JACK_OF_CLUBS),
    ]
)
def test_parse_card_valid(text, expected):
    assert parse_card(text) is expected


@pytest.mark.parametrize(
    "text",
    [
        # ---- Empty / whitespace ----
        "",
        " ",
        "   ",
        "\t",
        "\n",

        # ---- Missing rank or suit ----
        "Ace",
        "Spades",
        "Queen",
        "10",
        "♠",

        # ---- Invalid ranks ----
        "One of Spades",
        "Eleven of Hearts",
        "14 of Clubs",
        "0 of Diamonds",
        "1 of Hearts",

        # ---- Invalid suits ----
        "Ace of Flowers",
        "King of Cups",
        "Queen of Stars",

        # ---- Garbled formats ----
        "Ace Spades Hearts",
        "AceSpades", ###
        "♠A",
        "SA",
        "S A",
        "A♠♠",

        # ---- Typos / near-misses ----
        "Aec of Spades",
        "Ace of Spade"
        "Quen of Hearts",
        "Jack Spade Club",

        # ---- Wrong separators / punctuation ----
        "Ace, of Spades",
        "Ace/of/Spades",
        "Ace.of.Spades",

        # ---- Extra words ----
        "Give Ace of Spades"
        "Ace of Spades is coolest"

        # ---- Unicode but malformed ----
        "A♥♠",
        "♥ of Hearts",
    ],
)
def test_parse_card_invalid(text):
    with pytest.raises(ValueError):
        parse_card(text)

@pytest.mark.parametrize(
    "text",
    [
        # ---- Not strings ----
        None,
        42,
        3.14,
        [],
        {},
    ],
)
def test_parse_card_invalid_type(text):
    with pytest.raises(TypeError):
        parse_card(text)  # type: ignore


@pytest.mark.parametrize(
    "text, expected_count",
    [
        # perfectly parseable
        ("Queen of Spades Jack of Diamonds", 2),
        ("Ace of Clubs Two of Clubs Three of Clubs", 3),
        ("Ace of Clubs, Two of Clubs, Three of Clubs", 3),
        ("King of Hearts and Queen of Hearts", 2),
        ("King of Spades or Queen of Spades", 2),
        ("A♠ Q♥ 10♦", 3),
        ("A♠; Q♥; 10♦", 3),
        ("Jack of Hearts / Ten of Hearts", 2),
        ("[A♣; K♣; Q♣]", 3),

        # Nonsense words in between cards
        ("Ace of Spades NotACard Queen of Hearts", 2),
        ("Seven of Diamonds Foo Bar Eight of Diamonds", 2),
        ("Nine of Clubs ??? Ten of Clubs", 2),
        ("Ace of Spades, NotACard, Queen of Hearts", 2),
        ("Seven of Diamonds, Foo Bar, Eight of Diamonds", 2),

        # ambiguous spacing / missing 'of'
        ("Ace Spades Jack Diamonds", 2),
        ("Queen Hearts King Hearts", 2),

        # Python output
        ("CardSet(9♠ Q♦ 9♣ J♥ 9♥ T♣ 5♦)", 7),
        ("[<Card.NINE_OF_SPADES: 48>, <Card.QUEEN_OF_DIAMONDS: 25>]", 2),
        ("[<Card.NINE_OF_SPADES: 48>,\n<Card.QUEEN_OF_DIAMONDS: 25>]", 2),

        # empty or garbage input
        ("", 0),
        (" ", 0),
        ("No cards here!", 0),

        # mixed separators
        ("Ace♠/King♠|Queen♠,Jack♠;Ten♠", 5), # 0

        # unusual formatting
        ("A♠ Q♥,10♦; J♣|K♣", 5), # 1
        ("Ace♣\nTwo♣ Three♣", 3), # 0

        # unicode confusion
        ("A♥♠", 0),          # likely failure
        ("♥ of Hearts", 0),   # likely failure

        # repetition (allowed to count multiple times)
        ("Ace of Spades Ace of Spades", 2),
        ("Queen of Hearts Queen of Hearts Queen of Hearts", 3),
    ],
)
def test_semantic_parser_count(text, expected_count):
    result = parse_card_set(text)
    assert len(result) == expected_count
