import random
from typing import Iterable, List

from enums import Card

class CardSet:
    def __init__(self, cards: Iterable[Card] | None = None):
        """Initialize empty or with an iterable of cards."""
        self.cards: List[Card] = list(cards) if cards is not None else []

    @classmethod
    def standard_deck(cls) -> "CardSet":
        """Initialize with the standard ordered 52-card deck."""
        return cls(Card)

    # ------ Reorder cards --------

    def shuffle(self) -> None:
        """Shuffle cards in place."""
        random.shuffle(self.cards)

    def sort_by_suit(self) -> None:
        """
        Sort by suit first (Clubs, Diamonds, Hearts, Spades),
        then by rank (Ace low).
        """
        self.cards.sort(key=lambda c: (c.suit, c.rank))

    def sort_by_rank(self) -> None:
        """
        Sort by rank first (Ace low),
        then by suit (Clubs, Diamonds, Hearts, Spades).
        """
        self.cards.sort(key=lambda c: (c.rank, c.suit))

    # ------- Add / Remove Cards ------

    def add(self, *cards):
        """
        Adds cards to the CardSet.
        Can be called like:
            add(card1, card2, card3)
            add([card1, card2, card3])
        """
        if len(cards) == 1 and isinstance(cards[0], Iterable) and not isinstance(cards[0], Card):
            # Single iterable of cards
            to_add = list(cards[0])
        else:
            # Multiple card arguments
            to_add = list(cards)

        for c in to_add:
            if not isinstance(c, Card):
                raise TypeError(f"Expected Card, got {type(c)}")
        self.cards.extend(to_add)
        return to_add

    def draw(self, n: int | None = None):
        """
        Draw cards from the top of the CardSet.

        Usage:
            draw()      -> Card
            draw(n)     -> list[Card]
        """
        if n is None:
            if not self.cards:
                raise IndexError("Cannot draw from empty CardSet")
            return self.cards.pop(0)

        if n < 0:
            raise ValueError("n must be non-negative")
        if n > len(self.cards):
            raise IndexError("Not enough cards to draw")

        drawn = self.cards[:n]
        del self.cards[:n]
        return drawn

    # -------- Length ----------

    def __len__(self) -> int:
        return len(self.cards)

    @property
    def size(self) -> int:
        return len(self.cards)

    # -------- Formating --------

    def __getitem__(self, item):
        result = self.cards[item]
        return CardSet(result) if isinstance(item, slice) else result

    def format(self, style="long") -> str:
        if style == "short":
            return " ".join(c.short_name() for c in self.cards)
        if style == "long":
            return ", ".join(c.long_name() for c in self.cards)
        raise ValueError("style must be 'long' or 'short'")

    def __str__(self):
        return self.format("long")

    def __repr__(self):
        return f"CardSet({self.format('short')})"

    # Might add latter
    # is_empty --- not deck also works
    # peek() --- deck[0] already works

class Seat:

    def __init__(self, name = ""):
        self.name = name
        self.hand = CardSet()
        self.tablaue = CardSet()

class Table:

    def __init__(self, seats = 4):
        self.deck = CardSet.standard_deck()
        self.stack = CardSet()  # pile to draw from I didn't like draw.draw()
        self.discard = CardSet()
        self.seats = [Seat(n) for n in range(seats)]

def render_first(table):
    """
    Render a 4-player table in ASCII art.

    Parameters:
        table: Table object with
            table.seats[0] = North
            table.seats[1] = East
            table.seats[2] = South
            table.seats[3] = West
            Each seat has .hand (CardSet) with short names
        table.discard: CardSet
    """

    # Helper: split a hand into lines of 4 cards each
    def hand_lines(hand, per_line=4):
        cards = [c.short_name() for c in hand]  # using short card name
        lines = []
        for i in range(0, len(cards), per_line):
            lines.append(" ".join(cards[i:i+per_line]))
        return lines

    # Maximum number of lines per hand (for alignment)
    max_lines = 5  # 20 cards max, 4 per line

    north_lines = hand_lines(table.seats[0].hand)
    south_lines = hand_lines(table.seats[2].hand)
    east_lines  = hand_lines(table.seats[1].hand)
    west_lines  = hand_lines(table.seats[3].hand)

    # Pad hands to max_lines
    def pad_lines(lines):
        while len(lines) < max_lines:
            lines.append("")
        return lines

    north_lines = pad_lines(north_lines)
    south_lines = pad_lines(south_lines)
    east_lines  = pad_lines(east_lines)
    west_lines  = pad_lines(west_lines)

    # Width of left and right hands
    left_width = max(len(line) for line in west_lines)
    right_width = max(len(line) for line in east_lines)

    # Center discard card
    if table.discard:
        center_card = table.discard[-1].short_name()
        center_card = Card.ACE_OF_SPADES
    else:
        center_card = "__"

    center_block = f"|{center_card}|"

    # Horizontal spacing between hands and center
    h_space = 4

    # Render North
    north_str = " " * (left_width + h_space) + " " + "\n".join(north_lines)
    print(north_str)

    # Render middle rows: West | Center | East
    for w, e in zip(west_lines, east_lines):
        line = f"{w.ljust(left_width)}{' ' * h_space}{center_block}{' ' * h_space}{e.ljust(right_width)}"
        print(line)

    # Render South
    south_str = " " * (left_width + h_space) + " " + "\n".join(south_lines)
    print(south_str)

def init_grid(w, h, c=' ') -> List[List[String]]:
    return [[c for x in range(w)] for y in range(h)]

 '\n'.join(["".join(l) for l in s])

render = render_first

__all__ = ( ["CardSet", "Table", "Seat", "render"] )
