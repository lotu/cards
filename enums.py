from enum import IntEnum
from dataclasses import *
from typing import *


class Rank(IntEnum):
    ACE   = 1
    TWO   = 2
    THREE = 3
    FOUR  = 4
    FIVE  = 5
    SIX   = 6
    SEVEN = 7
    EIGHT = 8
    NINE  = 9
    TEN   = 10
    JACK  = 11
    QUEEN = 12
    KING  = 13

    @property
    def short(self) -> str:
        return {
            Rank.ACE:   "A",
            Rank.TWO:   "2",
            Rank.THREE: "3",
            Rank.FOUR:  "4",
            Rank.FIVE:  "5",
            Rank.SIX:   "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE:  "9",
            Rank.TEN:   "T",
            Rank.JACK:  "J",
            Rank.QUEEN: "Q",
            Rank.KING:  "K",
        }[self]

    @property
    def long(self) -> str:
        return self.name.title()

    def __str__(self) -> str:
        return self.long()

class Suit(IntEnum):
    CLUBS    = 0
    DIAMONDS = 1
    HEARTS   = 2
    SPADES   = 3

    @property
    def symbol(self) -> str:
        return {
            Suit.CLUBS:    "♣",
            Suit.DIAMONDS: "♢",
            Suit.HEARTS:   "♡",
            Suit.SPADES:   "♠",
        }[self]

    @property
    def long(self) -> str:
        return self.name.title()

    def __str__(self) -> str:
        return self.long()


class Card(IntEnum):
    ACE_OF_CLUBS   = 1
    TWO_OF_CLUBS   = 2
    THREE_OF_CLUBS = 3
    FOUR_OF_CLUBS  = 4
    FIVE_OF_CLUBS  = 5
    SIX_OF_CLUBS   = 6
    SEVEN_OF_CLUBS = 7
    EIGHT_OF_CLUBS = 8
    NINE_OF_CLUBS  = 9
    TEN_OF_CLUBS   = 10
    JACK_OF_CLUBS  = 11
    QUEEN_OF_CLUBS = 12
    KING_OF_CLUBS  = 13

    ACE_OF_DIAMONDS   = 14
    TWO_OF_DIAMONDS   = 15
    THREE_OF_DIAMONDS = 16
    FOUR_OF_DIAMONDS  = 17
    FIVE_OF_DIAMONDS  = 18
    SIX_OF_DIAMONDS   = 19
    SEVEN_OF_DIAMONDS = 20
    EIGHT_OF_DIAMONDS = 21
    NINE_OF_DIAMONDS  = 22
    TEN_OF_DIAMONDS   = 23
    JACK_OF_DIAMONDS  = 24
    QUEEN_OF_DIAMONDS = 25
    KING_OF_DIAMONDS  = 26

    ACE_OF_HEARTS   = 27
    TWO_OF_HEARTS   = 28
    THREE_OF_HEARTS = 29
    FOUR_OF_HEARTS  = 30
    FIVE_OF_HEARTS  = 31
    SIX_OF_HEARTS   = 32
    SEVEN_OF_HEARTS = 33
    EIGHT_OF_HEARTS = 34
    NINE_OF_HEARTS  = 35
    TEN_OF_HEARTS   = 36
    JACK_OF_HEARTS  = 37
    QUEEN_OF_HEARTS = 38
    KING_OF_HEARTS  = 39

    ACE_OF_SPADES   = 40
    TWO_OF_SPADES   = 41
    THREE_OF_SPADES = 42
    FOUR_OF_SPADES  = 43
    FIVE_OF_SPADES  = 44
    SIX_OF_SPADES   = 45
    SEVEN_OF_SPADES = 46
    EIGHT_OF_SPADES = 47
    NINE_OF_SPADES  = 48
    TEN_OF_SPADES   = 49
    JACK_OF_SPADES  = 50
    QUEEN_OF_SPADES = 51
    KING_OF_SPADES  = 52

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


class PlayerId(IntEnum):
    PLAYER_1 = 0
    PLAYER_2 = 1
    PLAYER_3 = 2
    PLAYER_4 = 3

    @classmethod
    def from_num(cls, num: int) -> "PlayerId":
        "Number is the 1 index human facing value"
        return cls(num - 1)

    @classmethod
    def from_index(cls, i: int) -> "PlayerId":
        "Index is 0 index for lists/arrays"
        return cls(i)

    @property
    def num(self) -> int:
        return self.value + 1

    @property
    def idx(self) -> int:
        return self.value

    def __str__(self) -> str():
        return f"Player {self.num}"

class SeatPart(IntEnum):
    HAND    = 0
    TABLEAU = 1

    def __str__(self) -> str:
        return self.name.title()

# --- CardMove Enums (Explicitly defined values) ---

class Location(IntEnum):
    P1_HAND    = 1
    P1_TABLEAU = 2
    P2_HAND    = 3
    P2_TABLEAU = 4
    P3_HAND    = 5
    P3_TABLEAU = 6
    P4_HAND    = 7
    P4_TABLEAU = 8
    STACK      = 9 # Logic depends on this being the first shared location
    DISCARD    = 10

    @classmethod
    def from_seat(cls, seat: PlayerId, part: SeatPart) -> "Location":
        if not isinstance(seat, PlayerId):
            seat = PlayerId.from_num(seat) # Really don't like this but shrug
        if not isinstance(part, SeatPart):
            raise TypeError("part must be a SeatPart")
        return cls((seat.idx) * 2 + part + 1) # XXX

    @property
    def shared(self) -> bool:
        return self.value >= STACK

    @property
    def player(self) -> Optional[PlayerId]: # TODO
        # Returns 1-4 for players, None for shared
        return PlayerId.from_num(((self.value - 1) // 2) + 1) if not self.shared else None

    @property
    def seat_part(self) -> Optional[SeatPart]:
        return  SeatPart((self.value - 1) % 2) if not self.shared else None

    def __str__(self) -> str:
        # 2. Format the Source and Target strings
        if self.shared:
            # Handles STACK, DISCARD, etc.
            name = self.name.lower()
            return f"the {name}"
        else:
            # Handles P1_HAND, P2_TABLEAU, etc.
            p_num = self.player
            part = "hand" if self.seat_part == HAND else "tableau"
            return f"{self.player}'s {self.seat_part.name.lower()}" # TODO

@dataclass
class CardMove:
    """A structured representation of a player's intent."""
    source: Location
    target: Location
    count: int = 1
    cards: Card | list[Card] = None 

    def __repr__(self):
        details = []
        if self.source: details.append(f"source={self.source.name}")
        if self.target: details.append(f"target={self.target.name}")
        if self.count > 1: details.append(f"count={self.count}")
        if self.cards: details.append(f"cards={self.cards}")
        return f"CardMove({', '.join(details)})"

    # TODO Dramatically simplify this it should just be moves x from y to z
    def __str__(self) -> str:
        """Returns a natural language description of the card_move."""

        # 1. Determine what is being moved
        if self.cards:
            if isinstance(self.cards, list):
                item = f"{', '.join(c.short_name() for c in self.cards)}"
            else:
                item = self.cards.short_name()
        else:
            item = f"{self.count} card{'s' if self.count > 1 else ''}"

        # 2. Format the Source and Target strings
        src_str = str(self.source) if self.source is not None else "anywhere"
        tgt_str = str(self.target) if self.target is not None else "unknown"

        # 3. Choose the verb based on the movement
        if self.source is None:
            verb = "moves"
        elif self.source == STACK:
            verb = "draws" 
        #elif self.source is not None and self.target is not None \
                #and not self.source.shared and not self.target.shared \
                #and self.source.player != self.target.player:
            #verb = "takes"
        elif self.target == DISCARD:
            verb = "discards"
        else:
            verb = "moves"

        return f"{verb} {item} from {src_str} to {tgt_str}"

@dataclass
class Say:
    text: str
    target: Optional[PlayerId] = None

    def __repr__(self):
        return f'Say("{self.text}", {self.target})'

class Order(IntEnum):
    NO_ORDER = 0
    RANDOM = 1
    ASC = 2
    DESC = 3

class CardProperty(IntEnum):
    NO_PROPERTY = 0
    RANK = 1
    SUIT = 2

@dataclass
class Sorting:
    property: CardProperty
    order: Order

@dataclass
class Reorder:
    target: Location
    sort: List[Sorting] = field(default_factory=list)

@dataclass
class Action:
    player: PlayerId
    intent: CardMove | Say | Reorder

    def __repr__(self):
        return f"Action({self.player}, {self.intent})"

# ONLY A TABLE can execute an action so I Must extend interpret_input
# ---------- Re-export enum members ----------


globals().update(Suit.__members__)
globals().update(Rank.__members__)
globals().update(Card.__members__)
globals().update(PlayerId.__members__)
globals().update(SeatPart.__members__)
globals().update(Location.__members__)
globals().update(Order.__members__)
globals().update(CardProperty.__members__)

__all__ = (
    ["Rank", "Suit", "Card", "PlayerId",  "SeatPart", "Location", "CardMove", 
     "Say", "Order", "CardProperty", "Sorting", "Reorder", "Action"]
    + list(Rank.__members__)
    + list(Suit.__members__)
    + list(Card.__members__)
    + list(PlayerId.__members__)
    + list(SeatPart.__members__)
    + list(Location.__members__)
    + list(Order.__members__)
    + list(CardProperty.__members__)
    
)


