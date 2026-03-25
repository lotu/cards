import re
from enums import *
import logging

logger = logging.getLogger(__name__)
debug = logger.debug


_RANK_ALIASES = {
    "A":     ACE,
    "ACE":   ACE,
    "2":     TWO,
    "TWO":   TWO,
    "3":     THREE,
    "THREE": THREE,
    "4":     FOUR,
    "FOUR":  FOUR,
    "5":     FIVE,
    "FIVE":  FIVE,
    "6":     SIX,
    "SIX":   SIX,
    "7":     SEVEN,
    "SEVEN": SEVEN,
    "8":     EIGHT,
    "EIGHT": EIGHT,
    "9":     NINE,
    "NINE":  NINE,
    "10":    TEN,
    "T":     TEN,
    "TEN":   TEN,
    "J":     JACK,
    "JACK":  JACK,
    "Q":     QUEEN,
    "QUEEN": QUEEN,
    "K":     KING,
    "KING":  KING,
}

_SUIT_ALIASES = {
    "C":        CLUBS,
    "CLUB":     CLUBS,
    "CLUBS":    CLUBS,
    "♣":        CLUBS,
    "♧":        CLUBS,

    "D":        DIAMONDS,
    "DIAMOND":  DIAMONDS,
    "DIAMONDS": DIAMONDS,
    "♦":        DIAMONDS,
    "♢":        DIAMONDS,

    "H":        HEARTS,
    "HEART":    HEARTS,
    "HEARTS":   HEARTS,
    "♥":        HEARTS,
    "❤":        HEARTS,
    "♡":        HEARTS,

    "S":        SPADES,
    "SPADE":    SPADES,
    "SPADES":   SPADES,
    "♠":        SPADES,
    "♤":        SPADES,
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
    s = re.sub(r"(?=[♣♧♦♢♡♥❤♠♤])|(?<=[♣♧♦♢♡♥❤♠♤])", " ", s)
    s = re.sub(r"\s*OF\s*", " ", s)  # Safe because none of the tokens contain 'of'

    # Match Short formats (e.g. Q♠, 10D, TS) 
    short_match = re.fullmatch(r"(10|[2-9AJQKT])\s*([CDHS♣♧♦♢♡♥❤♠♤])", s)
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
    words = re.split(r'''[^\w♣♧♦♢♡♥❤♠♤]+''', text)
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

###############################################################################
# 
#  Action Parsing

def parse_action(text: str, player_id: PlayerId) -> Optional[Action]:
    """
    Primary entry point. Orchestrates smaller parsers.
    Returns an Action .
    """
    # 1. Check for Chat
    say_intent = parse_say(text, player_id, {})
    if say_intent:
        return Action(player_id, say_intent)

    # 2. Check for Reordering
    reorder_intent = parse_reorder(text, player_id)
    if reorder_intent:
        return Action(player_id, reorder_intent)

    # 3. Check for Card Movement (Existing logic)
    move_intent = parse_card_move(text, player_id) # Renamed your old interpret_input
    if move_intent:
        return Action(player_id, move_intent)

    return None

def resolve_player_id(text: str, name_map: Dict[str, PlayerId]) -> Tuple[Optional[PlayerId], str]:
    """
    Attempts to identify a player at the start of a string.
    Returns (PlayerId, remaining_text).
    """
    s = text.lstrip() # Only strip left to preserve message spacing
    if not s:
        return None, text

    # 1. Hard-coded shorthand (Highest Priority)
    # Match "p1" or "player 1"
    p_match = re.match(r"^(?:p|player\s+)([1-4])\b\s*", s, re.IGNORECASE)
    if p_match:
        return PlayerId.from_num(int(p_match.group(1))), s[p_match.end():]

    # 2. Name Map (Longest match first to prevent "Jo" stealing "Joe")
    sorted_names = sorted(name_map.keys(), key=len, reverse=True)
    for name in sorted_names:
        if s.lower().startswith(name.lower()):
            # Word boundary check: ensure "Joe" doesn't match "Joelle"
            # It matches if it's the end of string OR next char isn't alphanumeric
            name_len = len(name)
            if name_len == len(s) or not s[name_len].isalnum():
                remaining = s[name_len:].lstrip()
                # If there's a single separator character like ':' or ',', skip it
                if remaining and remaining[0] in ":,-":
                    remaining = remaining[1:].lstrip()
                return name_map[name], remaining

    return None, text



def parse_say(text: str, actor: PlayerId, name_map: Dict[str, PlayerId]) -> Optional[Say]:
    s = text.strip()
    if not s:
        return None

    # Handle the "!" shorthand
    if s.startswith("!"):
        target, msg = resolve_player_id(s[1:], name_map)
        return Say(text=msg.strip(), target=target)

    # Verb patterns
    # Global verbs: No target resolution attempted
    if re.match(r"^(say|chat)\b", s, re.IGNORECASE):
        msg = re.sub(r"^(say|chat)\b\s*", "", s, flags=re.IGNORECASE)
        return Say(text=msg.strip(), target=None)

    # Targeted verbs: Target resolution is mandatory
    targeted_match = re.match(r"^(tell|whisper)\b\s*", s, re.IGNORECASE)
    if targeted_match:
        content = s[targeted_match.end():]
        target, msg = resolve_player_id(content, name_map)
        # If no target found, we treat the whole thing as the message
        # (or return None if you want to enforce targets for 'whisper')
        return Say(text=msg.strip(), target=target)

    return None

def parse_say_old(text: str, actor: PlayerId) -> Optional[Say]:
    """
    Pure function to extract a Say intent from text.
    Supports:
    - 'say <msg>' or 'chat <msg>'
    - 'tell p<n> <msg>' or 'whisper p<n> <msg>'
    - '!<msg>' or '!p<n> <msg>'
    """
    s = text.strip()
    if not s:
        return None

    # 1. Handle the "!" prefix shorthand
    if s.startswith("!"):
        content = s[1:].strip()
        # Check for targeted shorthand: !p2 hello
        match = re.match(r"^p([1-4])\b\s*(.*)", content, re.IGNORECASE)
        if match:
            return Say(text=match.group(2).strip(), target=PlayerId.from_num(int(match.group(1))))
        return Say(text=content)

    # 2. Handle Verb-based chat
    # Pattern: (verb) (optional target) (message)
    # Examples: "say hello", "tell p2 check the board"
    pattern = r"^(say|chat|tell|whisper)\s+(?:p([1-4])\b\s*)?(.*)"
    chat_match = re.match(pattern, s, re.IGNORECASE)

    if chat_match:
        verb = chat_match.group(1).lower()
        target_num = chat_match.group(2)
        message = chat_match.group(3).strip()

        debug(f'verb: {verb}, target: {target_num}, message: {message}')
        target = PlayerId.from_num(int(target_num)) if target_num else None

        # 'tell' and 'whisper' usually imply a target, but we'll be flexible
        return Say(text=message, target=target)

    return None

def parse_reorder(text: str, actor: PlayerId) -> Optional[Reorder]:
    """Pure function to extract sorting/shuffling intent."""
    # s = text.lower()
    # if "shuffle" in s:
    #     # Default to actor's hand if no location specified
    #     loc = P1_HAND if actor == PLAYER_1 else P2_HAND # Simplified for example
    #     return Reorder(target=loc, sort=[Sorting(NO_PROPERTY, RANDOM)])
    # if "sort" in s:
    #     # logic for identifying Rank vs Suit
    #     return Reorder(target=P1_HAND, sort=[Sorting(RANK, ASC)])
    return None

def parse_card_move(text: str, player_idx: PlayerId) -> Optional[CardMove]:
    s = text.lower().strip()
    if not s:
        return None

    # --- Setup Defaults ---
    my_hand    = Location.from_seat(player_idx, SeatPart.HAND)
    my_tableau = Location.from_seat(player_idx, SeatPart.TABLEAU)
    
    # Final CardMove Variables
    found_cards = []
    found_count = None
    source = None
    target = None


    # 1. EXTRACT LOCATIONS / PLAYERS (Prepositional Phrases)
    # Identify Player
    is_tableau = False
    is_discard = False
    is_stack = False

    pp_matches = re.finditer(
        #r"(from|to|in|on)\s+(p[1-4]('s)?|my)?\s*(the)?\s*(tableau|table|board|discard|hand|pile|stack|deck|draw pile])?", s)
        r"(from|to|in|on)\s+((?:player\s*|p)[1-4]('s)?|my)?\s*(the)?\s*(tableau|table|board|discard|hand|pile|stack|deck|draw pile])?", s)
    for pp_match in pp_matches:
        pp_player_num = None
        debug( f'pp_match 0: {pp_match.group(0)}, 1: {pp_match.group(1)}, 2: {pp_match.group(2)}, 3: {pp_match.group(3)}, 4: {pp_match.group(4)} ' )
        if pp_match.group(2):
            player_match = re.search(r'(?:player\s*|p)([1-4])', pp_match.group(2))
            pp_player_num = int(player_match.group(1)) if player_match else None
            if re.search(r'my', pp_match.group(2)):
                pp_player_num = player_idx
        
        
        # Identify Part (Tableau vs Hand)
        is_hand = pp_match.group(5) in ["hand"]
        is_tableau = pp_match.group(5) in ["tableau", "table", "board"]
        is_discard = pp_match.group(5) in ["discard", "pile"]
        is_stack = pp_match.group(5) in ["stack", "deck", "draw pile"]
        
        # Determine Source/Target based on Prepositions
        if pp_match.group(1) == "from":
            if pp_player_num:
                source = Location.from_seat(pp_player_num, SeatPart.TABLEAU if is_tableau else SeatPart.HAND)
            elif is_discard: source = DISCARD
            elif is_stack: source = STACK
            elif is_hand: source = my_hand
            elif is_tableau: source = my_tableau 
        
        if pp_match.group(1) in ["to", "in", "on"]:
            if pp_player_num:
                target = Location.from_seat(pp_player_num, SeatPart.TABLEAU if is_tableau else SeatPart.HAND)
            elif is_hand:    target = my_hand
            elif is_tableau: target = my_tableau
            elif is_discard: target = DISCARD

        debug (f"s: {source}, t: {target}, cs: {found_cards}, cn: {found_count}")
        # Cleanup string of the locations we found
        s = re.sub(pp_match.group(0), '', s)

    # 2. EXTRACT NOUN SPECIFIC CARDS (Most Specific)
    # We use parse_card_set, then remove those card names from the string 
    # so their ranks/suits don't interfere with "count" extrcard_move later.
    found_cards = parse_card_set(s)
    if found_cards:
        # Simple removal: this is a bit naive but works for standard card names
        for card in found_cards:
            s = s.replace(card.short_name().lower(), "")
            # Also try to remove long names if they were used
            s = s.replace(card.long_name().lower(), "")
            s = s.replace("of", "") # Remove 'of' left over from card names
        found_count = len(found_cards)
    else:
        # 3. EXTRACT NUMERIC QUANTITIES
        # Now that cards and player IDs are gone, any digit left is the count
        digit_match = re.search(r'\d+', s)
        if digit_match:
            found_count = int(digit_match.group())
        else:
            found_count = 1

    # 4. EXTRACT INTENT (The Verb)
    s = s.strip()
    # Taking CardMove default target is hand
    is_draw = any(k in s for k in ["draw", "take", "get", "grab", "hit", "pick"])
    is_steal = any(k in s for k in ["steal", "rob", "snatch"])
    # Giving card_moves Default source is hand 
    is_play = any(k in s for k in ["play", "put", "set", "lay", "place"])
    is_give = any(k in s for k in ["give", "transfer", "send"]) # XXX pass was in here but removed
    is_discard_card_move = any(k in s for k in ["discard", "trash", "dump", "throw"])

    debug (f"s: {source}, t: {target}, cs: {found_cards}, cn: {found_count}")
    debug(f"draw: {is_draw}, play: {is_play}, give: {is_give}, steal: {is_steal}, discard: {is_discard_card_move}")
    # If we got too many verbs this is nonsense/ non-parseable
    if [is_draw, is_steal, is_play, is_give, is_discard_card_move].count(True) > 1:
        return None

    # 5. RESOLVE LOGIC & DEFAULTS
    # Apply Intent-based Defaults

    # Giving card_moves default to hand unless a card is specified
    if (is_play or is_discard_card_move or is_give) and not found_cards:
        source = source or my_hand

    if is_play:
        target = target or my_tableau
    if is_discard_card_move:
        target = target or DISCARD
    if is_give:
        pass
        # Target must be another player; default to next player if not specified Not sure about default here
        #if not target:
            #target = Location.from_seat((player_idx.num % 4) + 1, SeatPart.HAND)

    if is_steal or is_draw:
        target = target or my_hand

    if not found_cards: # Only need a default if we aren't grabing specific cards
        if is_steal:
            pass
            # Source must be another player
           # if not source:
           #     target = Location.from_seat((player_idx.num % 4) + 1, SeatPart.HAND)
        if is_draw: # or not (is_play or is_give or is_discard_card_move):
            # Default fallback is a Draw card_move
            source = source or (DISCARD if is_discard else STACK) #sound not default like this

    debug (f"s: {source}, t: {target}, cs: {found_cards}, cn: {found_count}")
    # Final check: If we still don't have a source/target, the command was too vague
    # For card_moves where we are taking a specific card where the card is doesn't have 
    # to be specified it's infered from the table.
    if not source and not found_cards or not target:
        return None

    return CardMove(source=source, target=target, cards=found_cards, count=found_count)


