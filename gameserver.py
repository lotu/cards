import asyncio
import sys
import os
import re
from datetime import datetime
from google import genai
import logging 
from cards import Table, table_to_str, describe_table
from enums import *
from parse import *


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN) 
#logging.getLogger("parse").setLevel(logging.INFO)
#logger.setLevel(level=logging.DEBUG) 
debug = logger.debug
info = print

INSTRUCTIONS = f"""
You will be playing cards. 
Respond briefly with commands in the form of text.
The game server only keeps track of the cards it does not enforce any rules or turn order.
You, the players, are responsible for knowing and following the rules.
This means only acting when it is appropriate.
If it is not appropriate for you to act reply with "pass" to do nothing.  
You may communicate with other players with "Say <message>"

In the middle of the table are:
1. The stack, it is face down, the draw command defaults to the stack
2. The discard, it is face up, the discard command put cards here.

Each player has:
1. A hand, which is hidden.
2. A tableau, which is visible to all players, when you play a card it goes here.

Example commands to move cards: 
Draw 2 cards: Move the top two card of the stack to your hand
Discard ace of spades: Move the ace of spades to the discard pile
play 2♣: Put the 2 of clubs from your hand into your tableau
take 1 card from player 2: Move one random card from player 2's hand to your own
give player 1 3♣ 4♢: Move the three of clubs and the 4 of diamonds to player 1's hand

You my use Unicode or spell out the card names.

You will be playing with 3 other AIs.
If the rules are unclear come to an agreement as a group.  You are responsible for dealing
with any mistakes made by other players, the engine will not do that for you.

You will be player Go Fish

Rules of Go Fish:

* Player 1 starts 
* If you have a set of four matching cards, you may play it in your tableau
* If you need other cards to complete a set, you may ask another player for the specific cards.  
* That player must then give you all the cards you asked for.
* If you recive the cards you asked for, you may either lay dow a set or continue to play by asking the same or another player for cards.  
* As long as you get the cards you ask for you may keep going.
* If the player you asked doesn't have the cards you request, they should tell you to "Go Fish!"
* If you are told to "Go Fish," draw a card from the stack.  If it turns out to be the kind you asked for tell everyone what it is and add it to your hand.  Then continue to play by asking another player for specific cards.
* If you draw a card you didn't ask for, keep it and your turn is over.
* Play goes plyaer 1, 2, 3, 4 then back to player 1
* If you play the last card in your hand draw 1 card
* Play continues until the draw pile is empty 

WINNING:
Who every has play the most sets of cards wins

You are"""

# Abstract Player Class
class Player:
    def __init__(self, player: PlayerId, name: str = None):
        # TODO use Player ENUM
        self.id = player
        self.name = name if name is not None else f"{player}"

    def connect(self):
        """Initialize any necessary connections (pipes, API clients, etc)."""
        pass

    async def wait_for_input(self) -> str:
        """Wait for the player to provide a command string."""
        raise NotImplementedError

    def send_message(self, message):
        """Send game state or text to the player."""
        raise NotImplementedError

    def send_card_move(self, player, card_move):
        self.send_message(f"{player} {card_move}\n")

    def send_turn(self, turn_number):
        self.send_message(f"\n\n--- TURN {turn_number} ---\n")
        
    def send_table(self, t):
        # self.send_message(f"{table_to_str(t)}\n")
        self.send_message(f"{describe_table(t,self.id)}\n\n")


class FIFOPlayer(Player):
    def __init__(self, player_id, fifo_dir):
        super().__init__(player_id)
        self.out_path = os.path.join(fifo_dir, f"p{self.id.num}_out")
        self.in_path = os.path.join(fifo_dir, f"p{self.id.num}_in")
        
        self.fd_out = None
        self.fd_in = None
        self.input_buffer = ""
        self.last_input = ""

    def __repr__(self):
        return f"{self.id}:FIFOPlayer({self.name}, {self.out_path}, {self.in_path})"

    def connect(self):
        # Open Output (Non-blocking)
        self.fd_out = os.open(self.out_path, os.O_WRONLY | os.O_NONBLOCK)
        
        # Open Input in Non-Blocking mode
        # This allows us to "check" the pipe without hanging the whole script
        self.fd_in = os.open(self.in_path, os.O_RDONLY | os.O_NONBLOCK)
        debug(f"-> {self.name} fifo opened.")

    def send_table(self, t):
        self.send_message(f"{table_to_str(t)}\n")
        # self.send_message(f"{describe_table(t,self.id)}\n\n")

    def send_message(self, message):
        if self.fd_out is not None:
            try:
                os.write(self.fd_out, message.encode())
            except OSError:
                pass

    async def wait_for_input(self) -> str:
        """
        Polls the file descriptor for a complete line.
        This is much more reliable for FIFOs than StreamReader.
        """
        debug(f"{self.name} is waiting for input...")
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
                        
                        debug(f"{self.name} sent: {self.last_input}")
                        return self.last_input
            except BlockingIOError:
                # This just means there is no data to read right now
                pass
            except Exception as e:
                error(f"Read error on {self.name}: {e}")
            
            # Sleep a tiny bit to prevent 100% CPU usage while polling
            await asyncio.sleep(0.1)

class LLMPlayer(Player):
    def __init__(self, player_id, fifo_dir, api_key=None,
                 #model_id="gemini-2.5-flash"
                 # model_id="gemini-2.5-pro"
                 model_id="gemini-3.1-pro-preview"
                 ):
        super().__init__(player_id)
        # Gemini setup
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.chat_session = None
        self.pending_message = ""

        # Mirroring setup (using your FIFO structure)
        self.out_path = os.path.join(fifo_dir, f"p{self.id.num}_out")
        self.fd_out = None

    def __repr__(self):
        return f"{self.id}:LLMPlayer({self.name}, {self.model_id}, {self.out_path})"

    def connect(self):
        # 1. Initialize Gemini
        instructions = f"{INSTRUCTIONS} {self.name}."

        self.chat_session = self.client.aio.chats.create(
            model=self.model_id,
            config={'system_instruction': instructions}
        )

        # 2. Open the output FIFO for mirroring
        # We use Non-blocking so the server doesn't hang if no one is listening
        try:
            self.fd_out = os.open(self.out_path, os.O_WRONLY | os.O_NONBLOCK)
            debug(f"-> {self.name} mirroring to {self.out_path}")
        except OSError:
            error(f"-> {self.name} could not open mirror pipe (no listener).")

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
        self._write_to_mirror(f"[SERVER -> LLM]:\n{message}")

        # Buffer for the actual API call
        self.pending_message += message + "\n"

    # TODO This should return (Player, str)
    async def wait_for_input(self) -> str:
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

## 

class GameServer:
    def __init__(self, player_count=4, fifo_dir="fifo", test=False):
        print("=" * 80)
        print("Starting Game Server At: ", datetime.now())
        print("Players: ", player_count)
        print()
        print(INSTRUCTIONS)
        # UI Control Booleans
        self.show_text_desc = False
        self.show_grid_ui = True

        self.fifo_dir = fifo_dir
        if test:
            self.players = [FIFOPlayer(PlayerId.from_num(i), fifo_dir) for i in range(1, player_count + 1)]
        else:
            self.players = [
                LLMPlayer(PLAYER_1, fifo_dir),
                #FIFOPlayer(PLAYER_1, fifo_dir),
                #FIFOPlayer(PLAYER_2, fifo_dir),
                LLMPlayer(PLAYER_2, fifo_dir),
                LLMPlayer(PLAYER_3, fifo_dir),
                LLMPlayer(PLAYER_4, fifo_dir),
            ]
        self.turn_number = 1

        for p in self.players:
            print(p)
        print("=" * 80)
        print()
        
        # 1. Create the Table
        self.table = Table(seats=len(self.players))
        
        # Sync Table Seat names with Player names
        for i, player in enumerate(self.players): # TODO User PlayerId
            self.table.seats[i].name = player.name

    def setup_game(self):
        """Handles shuffling and dealing logic."""
        debug("Initializing deck and dealing cards...")
        
        # 1. Use standard deck and shuffle
        self.table.deck.shuffle()
        
        # 2. Deal each player 7 cards
        for seat in self.table.seats:
            seat.hand.add(self.table.deck.draw(7))
            
        # 3. Place remaining cards in the stack
        self.table.stack.add(self.table.deck.draw(len(self.table.deck)))

    async def broadcast_state(self):
        """Sends the board representation to all players."""
        for p in self.players:
            p.send_table(self.table)
            p.send_turn(self.turn_number)

    async def run_game(self):
        self.setup_game()
        for player in self.players:
            player.connect()
        
        try:
            while True:
                await self.broadcast_state()

                print(table_to_str(self.table))
                print()
                print(f"--- Turn {self.turn_number} ---")
                print()
                
                debug(f"Server: Waiting for players to acknowledge Turn {self.turn_number}...")
                
                # Wait for all players to send a line (ignoring the content for now)
                inputs = await asyncio.gather(*(p.wait_for_input() for p in self.players))

                # Pause for a bit 
                # print("press Enter", file=sys.stderr)
                # await asyncio.to_thread(input, "")
                # await asyncio.sleep(15)

                # TODO Need to have a way so that p1 isn't always interpreted first
                # Interpret each player's input
                # shuffled_inputs = random.shuffle(enumerate(inputs))
                for i, text in enumerate(inputs):
                    p = PlayerId.from_index(i)
                    # card move source
                    debug(f"{p}: sent: {text}")
                    for line in text.split('\n'):
                        action = parse_action(line, p)
                        if action:
                            debug(f"Executing action: {action}")
                            self.execute_action(action)
                
                self.turn_number += 1
        except KeyboardInterrupt:
            info("\nShutting down.")

    def get_name_map(self) -> dict[str, PlayerId]:
        """Creates a map of seat names to PlayerIds for name resolution."""
        return {
            seat.name: PlayerId.from_index(i) 
            for i, seat in enumerate(self.table.seats) if seat.name
        }

    def execute_action(self,  action: Action):
        """Dispatches the action intent to the appropriate handler."""
        intent = action.intent
        actor_id = action.player
        
        if isinstance(intent, Say):
            self.handle_say(actor_id, intent)
        elif isinstance(intent, CardMove):
            self.handle_card_move(actor_id, intent)

    def handle_card_move(self, actor_id: PlayerId, card_move: CardMove):
        if self.table.execute_card_move(card_move):
            print(actor_id, card_move)
            # Broadcast the move to everyone for transparency
            for p in self.players:
                p.send_card_move(actor_id, card_move)

    def handle_say(self, actor_id: PlayerId, say: Say):
        """Routes chat messages based on the presence of a target."""
        sender_name = self.players[actor_id.idx].name

        print(f"{sender_name}: {say.text}")
        if say.target is not None:
            # Targeted Whisper (Sender and Receiver see it)
            msg = f"[Whisper] {sender_name} -> {say.target}: {say.text}\n"
            self.players[say.target.idx].send_message(msg)

            # Show the sender that their message was sent
            if say.target != actor_id:
                self.players[actor_id.idx].send_message(msg)
        else:
            # Global Chat
            msg = f"[Chat] {sender_name}: {say.text}\n"
            for p in self.players:
                p.send_message(msg)

if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
