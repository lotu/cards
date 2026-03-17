import asyncio
import os
import re
from google import genai
from logging import debug
from cards import Table, table_to_str, describe_table
from enums import *
from parse import *

# Abstract Player Class
class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.name = f"Player {self.id}"
        self.last_input = ""

    def connect(self):
        """Initialize any necessary connections (pipes, API clients, etc)."""
        pass

    def send_message(self, message):
        """Send game state or text to the player."""
        raise NotImplementedError

    async def wait_for_input(self):
        """Wait for the player to provide a command string."""
        raise NotImplementedError

class FIFOPlayer:
    def __init__(self, player_id, fifo_dir):
        self.id = player_id
        self.name = f"Player {self.id}"
        self.out_path = os.path.join(fifo_dir, f"p{self.id}_out")
        self.in_path = os.path.join(fifo_dir, f"p{self.id}_in")
        
        self.fd_out = None
        self.fd_in = None
        self.input_buffer = ""
        self.last_input = ""

    def connect(self):
        # Open Output (Non-blocking)
        self.fd_out = os.open(self.out_path, os.O_WRONLY | os.O_NONBLOCK)
        
        # Open Input in Non-Blocking mode
        # This allows us to "check" the pipe without hanging the whole script
        self.fd_in = os.open(self.in_path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"-> {self.name} descriptors opened.")

    def send_message(self, message):
        if self.fd_out is not None:
            try:
                os.write(self.fd_out, message.encode())
            except OSError:
                pass

    async def wait_for_input(self):
        """
        Polls the file descriptor for a complete line.
        This is much more reliable for FIFOs than StreamReader.
        """
        print(f"DEBUG: {self.name} is waiting for input...")
        while True:
            try:
                # Read whatever is in the pipe buffer (up to 1024 bytes)
                chunk = os.read(self.fd_in, 1024).decode()
                
                if chunk:
                    self.input_buffer += chunk
                    
                    # Check if we have a full line (terminated by newline)
                    if "\n" in self.input_buffer:
                        lines = self.input_buffer.split("\n")
                        # Take the first complete line
                        self.last_input = lines[0].strip()
                        # Keep the remainder in the buffer
                        self.input_buffer = "\n".join(lines[1:])
                        
                        print(f"DEBUG: {self.name} sent: {self.last_input}")
                        return self.last_input
            except BlockingIOError:
                # This just means there is no data to read right now
                pass
            except Exception as e:
                print(f"Read error on {self.name}: {e}")
            
            # Sleep a tiny bit to prevent 100% CPU usage while polling
            await asyncio.sleep(0.1)

class LLMPlayer(Player):
    def __init__(self, player_id, fifo_dir, api_key=None, model_id="gemini-2.0-flash"):
        super().__init__(player_id)
        # Gemini setup
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.chat_session = None
        self.pending_message = ""

        # Mirroring setup (using your FIFO structure)
        self.out_path = os.path.join(fifo_dir, f"p{self.id}_out")
        self.fd_out = None

    def connect(self):
        # 1. Initialize Gemini
        instructions = (
            f"You are {self.name} playing a text-based card game. "
            "Respond brieflly with comands in the form of text.  You will have to "
            "respond every 'turn' as the gameserver does not enforce any rules (much like "
            "a pyscial table doesn't enforce the rules of a card game "
            "We are currentlly developing this system every turn please respond with an "
            "action described as text, please try diffrent things out."
 
        )
        self.chat_session = self.client.aio.chats.create(
            model=self.model_id,
            config={'system_instruction': instructions}
        )

        # 2. Open the output FIFO for mirroring
        # We use Non-blocking so the server doesn't hang if no one is listening
        try:
            self.fd_out = os.open(self.out_path, os.O_WRONLY | os.O_NONBLOCK)
            print(f"-> {self.name} mirroring to {self.out_path}")
        except OSError:
            print(f"-> {self.name} could not open mirror pipe (no listener).")

    def _write_to_mirror(self, text):
        """Helper to push text to the FIFO if open."""
        if self.fd_out is not None:
            try:
                os.write(self.fd_out, text.encode())
            except OSError:
                # Listener likely disconnected
                pass

    def send_message(self, message):
        """Messages from the server (Table state, game logs)."""
        # Mirror the incoming server message so we see what the LLM sees
        self._write_to_mirror(f"\n[SERVER -> LLM]:\n{message}\n")

        # Buffer for the actual API call
        self.pending_message += message + "\n"

    async def wait_for_input(self):
        if not self.pending_message:
            return ""

        prompt = self.pending_message
        self.pending_message = ""

        try:
            # Call the LLM
            response = await self.chat_session.send_message(prompt)
            self.last_input = response.text.strip()

            # Mirror the LLM's response to the FIFO
            self._write_to_mirror(f"\n[LLM -> SERVER]: {self.last_input}\n")

            return self.last_input
        except Exception as e:
            error_msg = f"!! LLM Error: {e}"
            self._write_to_mirror(f"\n{error_msg}\n")
            return "pass"

class GameServer:
    def __init__(self, player_count=4, fifo_dir="fifo"):
        # UI Control Booleans
        self.show_text_desc = False
        self.show_grid_ui = True

        self.fifo_dir = fifo_dir
        self.players = [Player(i, fifo_dir) for i in range(1, player_count + 1)]
        self.players = [
            FIFOPlayer(1, fifo_dir),
            LLMPlayer(2), # Uses environment variable for API key
            FIFOPlayer(3, fifo_dir),
            LLMPlayer(4)
        ]
        self.turn_number = 1
        
        # 1. Create the Table
        self.table = Table(seats=player_count)
        
        # Sync Table Seat names with Player names
        for i, player in enumerate(self.players):
            self.table.seats[i].name = player.name

    def setup_game(self):
        """Handles shuffling and dealing logic."""
        print("Initializing deck and dealing cards...")
        # 1. Use standard deck and shuffle
        self.table.deck.shuffle()
        
        # 2. Deal each player 7 cards
        for seat in self.table.seats:
            seat.hand.add(self.table.deck.draw(7))
            
        # 3. Place remaining cards in the stack
        self.table.stack.add(self.table.deck.draw(len(self.table.deck)))

    async def broadcast_state(self):
        """Sends the board representation to all players."""
        output_parts = []
        
        output_parts.append(f"\n\n\n--- TURN {self.turn_number} ---\n")
        
        # Send representations based on booleans
        if self.show_text_desc:
            output_parts.append(describe_table(self.table))
            output_parts.append("\n")

        if self.show_grid_ui:
            output_parts.append(table_to_str(self.table))
            output_parts.append("\n")

        output_parts.append("\nPress [ENTER] in your input terminal to advance...")
        full_payload = "".join(output_parts)

        for p in self.players:
            p.send_message(full_payload)

    async def run_game(self):
        self.setup_game()
        for player in self.players:
            player.connect()
        
        try:
            while True:
                await self.broadcast_state()
                
                print(f"Server: Waiting for players to acknowledge Turn {self.turn_number}...")
                
                # Wait for all players to send a line (ignoring the content for now)
                inputs = await asyncio.gather(*(p.wait_for_input() for p in self.players))

                # TODO Need to have a way so that p1 isn't always interpreted first
                # Interpret each player's input
                for i, text in enumerate(inputs):
                    action = interpret_input(text, i)
                    if action:
                        print(f"Player {i+1} wants to: {action}")
                        try:
                            # 4. Execute
                            self.table.execute_action(action)
                        except ValueError as e:
                            self.players[i].send_message(f"Invalid move: {e}\n")
                
                self.turn_number += 1
        except KeyboardInterrupt:
            print("\nShutting down.")


def interpret_input_simple(text: str, player_idx: int, table) -> Optional[Action]:
    """
    Parses natural language into structured Actions, supporting player-to-player
    and player-to-table interactions.
    """
    s = text.lower().strip()
    if not s:
        return None

    # Constants for the acting player
    my_seat_num = player_idx + 1
    my_hand = Location.from_seat(my_seat_num, SeatPart.HAND)
    my_tableau = Location.from_seat(my_seat_num, SeatPart.TABLEAU)

    # 1. Identify if another player is mentioned (e.g., "p2")
    player_match = re.search(r'p([1-4])', s)
    other_seat_num = int(player_match.group(1)) if player_match else None

    # Identify if 'tableau' or 'table' is mentioned
    is_tableau = any(k in s for k in ["tableau", "table", "board"])
    target_part = SeatPart.TABLEAU if is_tableau else SeatPart.HAND

    # --- Case A: Playing a card to your own Tableau ("play Ace") ---
    if "play" in s or ("put" in s and is_tableau and not other_seat_num):
        try:
            card = parse_card_set(s)
            return Action(source=my_hand, target=my_tableau, cards=card)
        except ValueError:
            pass

    # --- Case B: Taking/Stealing from another player ("take from p2") ---
    if any(k in s for k in ["take", "steal", "grab", "get"]) and other_seat_num:
        source_loc = Location.from_seat(other_seat_num, target_part)
        return Action(source=source_loc, target=my_hand, count=1)

    # --- Case C: Giving to another player ("give Ace to p2") ---
    if any(k in s for k in ["give", "pass", "put"]) and other_seat_num:
        target_loc = Location.from_seat(other_seat_num, target_part)
        try:
            card = parse_card_set(s)
            return Action(source=my_hand, target=target_loc, cards=card)
        except ValueError:
            return Action(source=my_hand, target=target_loc, count=1)

    # --- Case D: Existing Draw Logic (Stack / Discard) ---
    if any(k in s for k in ["draw", "take", "get", "grab", "hit"]):
        count_match = re.search(r'\d+', s)
        count = int(count_match.group()) if count_match else 1
        source = DISCARD if ("discard" in s or "pile" in s) else STACK
        return Action(source=source, target=my_hand, count=count)

    # --- Case E: Picking specific card from Discard ---
    if len(table.discard.cards) > 0:
        try:
            card = parse_card(s)
            if card == table.discard.cards[-1]:
                return Action(source=DISCARD, target=my_hand, cards=card)
        except ValueError:
            pass

    return None

def interpret_input(text: str, player_idx: int) -> Optional[Action]:
    s = text.lower().strip()
    if not s:
        return None

    # --- Setup Defaults ---
    my_seat_num = player_idx + 1
    my_hand    = Location.from_seat(my_seat_num, SeatPart.HAND)
    my_tableau = Location.from_seat(my_seat_num, SeatPart.TABLEAU)
    
    # Final Action Variables
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
        r"(from|to|in|on)\s+(p[1-4]('s)?|my)?\s*(the)?\s*(tableau|table|board|discard|hand|pile|stack|deck|draw pile])?", s)
    for pp_match in pp_matches:
        pp_player_num = None
        debug( f'pp_match 0: {pp_match.group(0)}, 1: {pp_match.group(1)}, 2: {pp_match.group(2)}, 3: {pp_match.group(3)}, 4: {pp_match.group(4)} ' )
        if pp_match.group(2):
            player_match = re.search(r'p([1-4])', pp_match.group(2))
            pp_player_num = int(player_match.group(1)) if player_match else None
            if re.search(r'my', pp_match.group(2)):
                pp_player_num = my_seat_num
        
        
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
    # so their ranks/suits don't interfere with "count" extraction later.
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
    # Taking Action default target is hand
    is_draw = any(k in s for k in ["draw", "take", "get", "grab", "hit", "pick"])
    is_steal = any(k in s for k in ["steal", "rob", "snatch"])
    # Giving actions Default source is hand 
    is_play = any(k in s for k in ["play", "put", "set", "lay", "place"])
    is_give = any(k in s for k in ["give", "pass", "transfer", "send"])
    is_discard_action = any(k in s for k in ["discard", "trash", "dump", "throw"])

    debug (f"s: {source}, t: {target}, cs: {found_cards}, cn: {found_count}")
    debug(f"draw: {is_draw}, play: {is_play}, give: {is_give}, steal: {is_steal}, discard: {is_discard_action}")
    # If we got too many verbs this is nonsense/ non-parseable
    if [is_draw, is_steal, is_play, is_give, is_discard_action].count(True) > 1:
        return None

    # 5. RESOLVE LOGIC & DEFAULTS
    # Apply Intent-based Defaults

    # Giving actions default to hand unless a card is specified
    if (is_play or is_discard_action or is_give) and not found_cards:
        source = source or my_hand

    if is_play:
        target = target or my_tableau
    if is_discard_action:
        target = target or DISCARD
    if is_give:
        # Target must be another player; default to next player if not specified Not sure about default here
        if not target:
            target = Location.from_seat((my_seat_num % 4) + 1, SeatPart.HAND)

    if is_steal or is_draw:
        target = target or my_hand

    if not found_cards: # Only need a default if we aren't grabing specific cards
        if is_steal:
            # Source must be another player
            if not source:
                target = Location.from_seat((my_seat_num % 4) + 1, SeatPart.HAND)
        if is_draw: # or not (is_play or is_give or is_discard_action):
            # Default fallback is a Draw action
            source = source or (DISCARD if is_discard else STACK) #sound not default like this

    debug (f"s: {source}, t: {target}, cs: {found_cards}, cn: {found_count}")
    # Final check: If we still don't have a source/target, the command was too vague
    # For actions where we are taking a specific card where the card is doesn't have 
    # to be specified it's infered from the table.
    if not source and not found_cards or not target:
        return None

    return Action(source=source, target=target, cards=found_cards, count=found_count)

if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
