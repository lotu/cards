import pytest

from enums import *
from cards import *

# ------------------------

# Table
def test_table():
    t = Table()
    # Ensure cards are in standard order
    assert t.deck[0] == ACE_OF_CLUBS
    assert t.deck[15]== THREE_OF_DIAMONDS
    assert t.deck[-1] == KING_OF_SPADES

def test_draw_methods():
    t = init_table() # asserts run here

def init_table(): # Same table as from test draw methods
    t = Table()

    t.seats[0].name = "Player 1"

    t.seats[0].hand.add(t.deck.draw(13))
    t.seats[1].hand.add(t.deck.draw(13))
    # seat 2 avoided on purpose
    t.seats[3].hand.add(t.deck.draw(13))

    t.stack.add(t.deck.draw(13))
    assert t.seats[0].hand.size == 13
    assert t.seats[1].hand.size == 13
    assert t.seats[2].hand.size == 0 
    assert t.seats[3].hand.size == 13

    assert t.seats[0].hand[0] == ACE_OF_CLUBS
    assert t.seats[0].hand[12] == KING_OF_CLUBS
    assert t.seats[0].hand[-1] == KING_OF_CLUBS
    assert t.seats[1].hand[-1] == KING_OF_DIAMONDS
    assert t.seats[3].hand[-1] == KING_OF_HEARTS

    assert t.stack[0] == ACE_OF_SPADES

    assert TEN_OF_CLUBS in t.seats[0].hand
    assert not TEN_OF_CLUBS in t.discard

    t.discard.add(t.seats[0].hand.pick(TEN_OF_CLUBS))

    assert t.seats[0].hand.size == 12
    assert not TEN_OF_CLUBS in t.seats[0].hand
    assert TEN_OF_CLUBS in t.discard

    t.seats[1].tableau.add(t.seats[1].hand.pick([  ACE_OF_DIAMONDS
                                                 , THREE_OF_DIAMONDS
                                                 , JACK_OF_DIAMONDS
                                                 , KING_OF_SPADES]))

    return t

def test_hand_lines():
    t = init_table()
    grid = hand_lines(t.seats[0].hand)
    assert grid == ['A♣ 2♣ 3♣ 4♣',  '5♣ 6♣ 7♣ 8♣', '9♣ J♣ Q♣ K♣']

    grid = hand_lines(t.seats[2].hand)
    assert grid == []

    grid = hand_lines(t.seats[3].hand)
    assert grid == ['A♥ 2♥ 3♥ 4♥',  '5♥ 6♥ 7♥ 8♥', '9♥ T♥ J♥ Q♥', 'K♥']


def test_pad_grid():
    t = init_table()
    grid = pad_grid(hand_lines(t.seats[0].hand))
    assert grid == ['A♣ 2♣ 3♣ 4♣',  '5♣ 6♣ 7♣ 8♣', '9♣ J♣ Q♣ K♣']

    grid = pad_grid(hand_lines(t.seats[2].hand))
    assert grid == []

    grid = pad_grid(hand_lines(t.seats[3].hand))
    assert grid == ['A♥ 2♥ 3♥ 4♥',  '5♥ 6♥ 7♥ 8♥', '9♥ T♥ J♥ Q♥', 'K♥         ']

def test_seat_to_grid():
    t = init_table()
    s = grid_to_str(seat_to_grid(t.seats[0]))
    assert s == \
"""           
           
           
           
-----------
A♣ 2♣ 3♣ 4♣
5♣ 6♣ 7♣ 8♣
9♣ J♣ Q♣ K♣
           
Player 1   """

def test_full_grid():
    t = init_table()
    s = table_to_str(t)
