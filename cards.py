import random
from typing import Iterable, List

from enums import *

##

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
            add(card1,  card2, card3)
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
        Draw cards from the top always 0 index first of the CardSet.

        Usage:
            draw()      -> Card
            draw(n)     -> list[Card]
        """
        if isinstance(n, Card):
            raise ValueError("Draw takes numbers not specific cards")
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

    def pick(self, *cards):
        """
        Remove & Return  cards to the CardSet.
        Can be called like:
            pick(card1,  card2, card3)
            pick([card1, card2, card3])
        """
        if len(cards) == 1 and isinstance(cards[0], Iterable) and not isinstance(cards[0], Card):
            # Single iterable of cards
            to_pick = list(cards[0])
        else:
            # Multiple card arguments
            to_pick = list(cards)


        picked = []
        for c in to_pick:
            if not isinstance(c, Card):
                raise TypeError(f"Expected Card, got {type(c)}")
            try:
                index = self.cards.index(c)
                picked.append( self.cards.pop(index))
            except ValueError:
                pass # Card not present

        return picked

    def pull(self, n: int = None):
        """
        Remove & Return n random cards.
        Doesn't disturm order.
        """
        if n is None:
            if len(self.cards) > 0:
                return self.cards.pop(random.randrange(len(self.cards)))
            else:
                raise IndexError("Empty of cards")
        if len(self.cards) < n:
            raise IndexError("Not enough cards to pull.")
        pulled = []
        for i in range(n):
                pulled.append(self.cards.pop(random.randrange(len(self.cards))))
        return pulled

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
    ##

class Seat:

    def __init__(self, name = ""):
        self.name = str(name)
        self.hand = CardSet()
        self.tableau = CardSet()

class Table:

    def __init__(self, seats = 4, empty=False):
        self.deck = CardSet.standard_deck() if not empty else CardSet()
        self.stack = CardSet()  # pile to draw from I didn't like draw.draw()
        self.discard = CardSet()
        self.seats = [Seat(n) for n in range(seats)]

    def __str__(self) -> str:
        return ''

    def _get_cardset(self, location: Location):
        """Resolves a Location enum to a physical CardSet instance on the table."""
        if location == Location.STACK:
            return self.stack
        if location == Location.DISCARD:
            return self.discard

        # Player-specific locations (P1-P4)
        seat_idx = location.player - 1
        seat = self.seats[seat_idx]

        if location.seat_part == SeatPart.HAND:
            return seat.hand
        else:
            return seat.tableau

    def execute_action(self, action: Action) -> bool:
        """Performs the physical movement of cards defined by the Action."""
        source = self._get_cardset(action.source)
        target = self._get_cardset(action.target)

        # Case 1: Moving a specific named card (e.g., from Discard)
        if action.cards:
            cards = target.add(source.pick(action.cards))
            return cards

        # Case 2: Moving a quantity of cards (e.g., Drawing from Stack)
        else:
            # We draw whatever is available up to the requested count
            actual_count = min(len(source.cards), action.count)
            if len(source) >= action.count:
                target.add( source.draw(actual_count) )
            else:
                return False

        return True
   ##

def table_to_str(t):
    grid = init_grid(45,30)

    replace_subgrid(grid,seat_to_grid(t.seats[0]),15,20)
    replace_subgrid(grid,seat_to_grid(t.seats[1]), 1,10)
    replace_subgrid(grid,seat_to_grid(t.seats[2]),15, 0)
    replace_subgrid(grid,seat_to_grid(t.seats[3]),35,10)

    replace_subgrid(grid,card_grid(str(len(t.stack))), 20, 13)
    replace_subgrid(grid,card_grid(
        t.discard[-1] if len(t.discard) > 0 else ''), 20, 18)

    return grid_to_str(grid)

## 
def describe_table(t: Table) -> str:
    """Returns a readable summary of the current table state."""
    description = []

    # Central Piles
    description.append("--- Central Piles ---")
    description.append(f"Stack: {len(t.stack)} cards remaining.")
    description.append(f"Discard Pile: {t.discard.format('short') if t.discard else 'Empty'}")
    description.append("")

    # Player Seats
    description.append("--- Player Seats ---")
    for i, seat in enumerate(t.seats):
        name = seat.name if seat.name else f"Player {i}"

        # Format Hand and Tableau
        hand_str = seat.hand.format("short") if seat.hand else "Empty"
        tableau_str = seat.tableau.format("short") if seat.tableau else "Empty"

        description.append(f"Seat {i} ({name}):")
        description.append(f"  Hand:    {len(seat.hand)} cards")
        description.append(f"  Tableau: [{tableau_str}]")
        description.append("-" * 20)

    return "\n".join(description)
##
def seat_to_grid(s):
    grid = init_grid(11,10)
    tableau = hand_lines(s.tableau)
    grid = replace_subgrid(grid, hand_lines(s.tableau), 0, 0) 
    grid = replace_subgrid(grid, ['-' * 11 ], 0, 4) 
    grid = replace_subgrid(grid, hand_lines(s.hand), 0, 5) 
    grid = replace_subgrid(grid, [ s.name ], 0, 9)
    return grid
##
def card_grid(str_value):
    if isinstance(str_value, Card):
        str_value = str_value.short_name()
    g = '''┌──┐
│  │
└──┘'''
    grid = [list(line) for line in g.split('\n')]
    if len(str_value) == 2:
       grid[1][1] = str_value[0]
       grid[1][2] = str_value[1]
    if len(str_value) == 1:
       grid[1][2] = str_value[0]
    return grid


##

# Helper: split a hand into lines of 4 cards each
def hand_lines(hand, per_line=4):
    cards = [c.short_name() for c in hand]  # using short card name
    lines = []
    for i in range(0, len(cards), per_line):
        lines.append(" ".join(cards[i:i+per_line]))
    return lines
##

##
def init_grid(w, h, c=' ') -> list[list[str]]:
    return [[c for x in range(w)] for y in range(h)]

 ##
def grid_to_str(grid) -> str:
    return '\n'.join(["".join(line) for line in grid])
##

def pad_grid(grid, padding=' ', length = 0):
    """ Add padding to string """
    if not grid:
        return grid

    pad_to = max( length, max([len(line) for line in grid]) ) if len(grid) != 0 else  0
 
    # Add enough padding to each line make pad_to long.
    if isinstance(grid[0], str):
        return [line + padding * (pad_to - len(line))  for line in grid]
    else:
        return [line + [ padding  for _ in range (pad_to - len(line))]  for line in grid]

##

def str_list_to_grid(str_list):
    return [list(line) for line in replacement]

def replace_subgrid(original, replacement, start_col, start_row):
    """
    Replaces a portion of 'original' with 'replacement' starting at 
    (start_row, start_col).
    """
    if not replacement:
        return original

    # Ensure replacement is a list of lists of characters
    # This handles cases where replacement might be a list of strings
    formatted_replacement = [list(line) for line in pad_grid(replacement)]
    
    rows_to_replace = len(formatted_replacement)
    cols_to_replace = len(formatted_replacement[0])

    for i in range(rows_to_replace):
        for j in range(cols_to_replace):
            target_row = start_row + i
            target_col = start_col + j
            
            # Boundary check: don't write outside the original grid
            if target_row < len(original) and target_col < len(original[0]):
                original[target_row][target_col] = formatted_replacement[i][j]
                
    return original

##


# __all__ = ( ["CardSet", "Table", "Seat", ] )
