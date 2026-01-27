import random
from typing import Iterable, List

from .enums import Card

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

