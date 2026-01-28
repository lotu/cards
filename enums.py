from enum import IntEnum


class Rank(IntEnum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    @property
    def short(self) -> str:
        return {
            Rank.ACE: "A",
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "T",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
        }[self]

    @property
    def long(self) -> str:
        return self.name.title()


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def symbol(self) -> str:
        return {
            Suit.CLUBS: "♣",
            Suit.DIAMONDS: "♦",
            Suit.HEARTS: "♥",
            Suit.SPADES: "♠",
        }[self]

    @property
    def long(self) -> str:
        return self.name.title()


class Card(IntEnum):
    ACE_OF_CLUBS = 1
    TWO_OF_CLUBS = 2
    THREE_OF_CLUBS = 3
    FOUR_OF_CLUBS = 4
    FIVE_OF_CLUBS = 5
    SIX_OF_CLUBS = 6
    SEVEN_OF_CLUBS = 7
    EIGHT_OF_CLUBS = 8
    NINE_OF_CLUBS = 9
    TEN_OF_CLUBS = 10
    JACK_OF_CLUBS = 11
    QUEEN_OF_CLUBS = 12
    KING_OF_CLUBS = 13

    ACE_OF_DIAMONDS = 14
    TWO_OF_DIAMONDS = 15
    THREE_OF_DIAMONDS = 16
    FOUR_OF_DIAMONDS = 17
    FIVE_OF_DIAMONDS = 18
    SIX_OF_DIAMONDS = 19
    SEVEN_OF_DIAMONDS = 20
    EIGHT_OF_DIAMONDS = 21
    NINE_OF_DIAMONDS = 22
    TEN_OF_DIAMONDS = 23
    JACK_OF_DIAMONDS = 24
    QUEEN_OF_DIAMONDS = 25
    KING_OF_DIAMONDS = 26

    ACE_OF_HEARTS = 27
    TWO_OF_HEARTS = 28
    THREE_OF_HEARTS = 29
    FOUR_OF_HEARTS = 30
    FIVE_OF_HEARTS = 31
    SIX_OF_HEARTS = 32
    SEVEN_OF_HEARTS = 33
    EIGHT_OF_HEARTS = 34
    NINE_OF_HEARTS = 35
    TEN_OF_HEARTS = 36
    JACK_OF_HEARTS = 37
    QUEEN_OF_HEARTS = 38
    KING_OF_HEARTS = 39

    ACE_OF_SPADES = 40
    TWO_OF_SPADES = 41
    THREE_OF_SPADES = 42
    FOUR_OF_SPADES = 43
    FIVE_OF_SPADES = 44
    SIX_OF_SPADES = 45
    SEVEN_OF_SPADES = 46
    EIGHT_OF_SPADES = 47
    NINE_OF_SPADES = 48
    TEN_OF_SPADES = 49
    JACK_OF_SPADES = 50
    QUEEN_OF_SPADES = 51
    KING_OF_SPADES = 52

    @classmethod
    def from_rank_suit(cls, rank: Rank, suit: Suit) -> "Card":
        if not isinstance(rank, Rank):
            raise TypeError("rank must be a Rank")
        if not isinstance(suit, Suit):
            raise TypeError("suit must be a Suit")
        return cls(suit * 13 + rank)

    @property
    def rank(self) -> Rank:
        return Rank((self.value - 1) % 13 + 1)

    @property
    def suit(self) -> Suit:
        return Suit((self.value - 1) // 13)

    def long_name(self) -> str:
        return f"{self.rank.long} of {self.suit.long}"

    def short_name(self) -> str:
        return f"{self.rank.short}{self.suit.symbol}"

    def __str__(self) -> str:
        return self.long_name()

# ---------- Re-export enum members ----------


globals().update(Suit.__members__)
globals().update(Rank.__members__)
globals().update(Card.__members__)

__all__ = (
    ["Rank", "Suit", "Card"]
    + list(Rank.__members__)
    + list(Suit.__members__)
    + list(Card.__members__)
)


