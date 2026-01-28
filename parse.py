
import re
from enums import *


_RANK_ALIASES = {
    "A": ACE,
    "ACE": ACE,
    "2": TWO,
    "TWO": TWO,
    "3": THREE,
    "THREE": THREE,
    "4": FOUR,
    "FOUR": FOUR,
    "5": FIVE,
    "FIVE": FIVE,
    "6": SIX,
    "SIX": SIX,
    "7": SEVEN,
    "SEVEN": SEVEN,
    "8": EIGHT,
    "EIGHT": EIGHT,
    "9": NINE,
    "NINE": NINE,
    "10": TEN,
    "T": TEN,
    "TEN": TEN,
    "J": JACK,
    "JACK": JACK,
    "Q": QUEEN,
    "QUEEN": QUEEN,
    "K": KING,
    "KING": KING,
}

_SUIT_ALIASES = {
    "C": CLUBS,
    "CLUB": CLUBS,
    "CLUBS": CLUBS,
    "♣": CLUBS,

    "D": DIAMONDS,
    "DIAMOND": DIAMONDS,
    "DIAMONDS": DIAMONDS,
    "♦": DIAMONDS,

    "H": HEARTS,
    "HEART": HEARTS,
    "HEARTS": HEARTS,
    "♥": HEARTS,

    "S": SPADES,
    "SPADE": SPADES,
    "SPADES": SPADES,
    "♠": SPADES,
}


def parse_card(text: str) -> Card:
    """
    Parse a card name in many formats and return a Card enum.

    Examples:
        parse_card("Ace of Spades")
        parse_card("Q♠")
        parse_card("queen_of_hearts")
        parse_card("10d")
    """
    if not isinstance(text, str):
        raise TypeError("Card text must be a string")

    # Remove leading trailing whitespace and upppercase 
    s = text.strip().upper()

    # Turn all seperators _, \, -, of into spaces
    s = re.sub(r"[_\-]", " ", s)
    s = re.sub(r"(?=[♣♦♥♠])|(?<=[♣♦♥♠])", " ", s)
    s = re.sub(r"\s*OF\s*", " ", s)  # Safe because none of the tokens contain 'of'

    # Match Short formats (e.g. Q♠, 10D, TS) 
    short_match = re.fullmatch(r"(10|[2-9AJQKT])\s*([CDHS♣♦♥♠])", s)
    if short_match:
        rank_text, suit_text = short_match.groups()
        rank = _RANK_ALIASES[rank_text]
        suit = _SUIT_ALIASES[suit_text]
        return Card.from_rank_suit(rank, suit)

    # Word-based formats
    parts = s.split()
    if len(parts) != 2:
        raise ValueError(f"Could not parse card: {text!r}")

    try:
        rank = _RANK_ALIASES[parts[0]]
        suit = _SUIT_ALIASES[parts[1]]
    except KeyError:
        raise ValueError(f"Invalid card description: {text!r}") from None

    return Card.from_rank_suit(rank, suit)

def parse_card_set(text: str) -> list[Card]:
    # Split on non Word (alpha numeraci)  characters except the suits
    words = re.split(r'''[^\w♠♦♣♥]+''', text)
    i = 0
    cards = []

    while i < len(words):
        matched = False

        for size in (1,2,3):
            chunk = " ".join(words[i:i+size])
            try:
                card = parse_card(chunk)
            except ValueError:
                continue
            cards.append(card)
            i += size
            matched = True
            break

        if not matched:
            i += 1

    return cards
