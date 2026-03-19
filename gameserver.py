import asyncio
import os
import re
from google import genai
from cards import Table, table_to_str, describe_table
from enums import *
from parse import *

# Abstract Player Class
class Player:
    def __init__(self, player_id):
        # TODO use Player ENUM
        self.player = PlayerId.from_num(player_id)
        self.id = player_id
        self.name = f"Player {self.id}"

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
        self.send_message(f"\n\n\n--- TURN {turn_number} ---\n")
        
    def send_table(self, t):
        # self.send_message(f"{table_to_str(t)}\n")
        self.send_message(f"{describe_table(t,self.player)}\n")


class FIFOPlayer(Player):
    def __init__(self, player_id, fifo_dir):
        super().__init__(player_id)
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

    async def wait_for_input(self) -> str:
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
    def __init__(self, player_id, fifo_dir, api_key=None, model_id="gemini-2.5-flash-lite"):
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
            "Respond brieflly with comands in the form of text. Example commands are draw 2 cards "
            "Discard ace of spades, play a card, or take 1 card from player 2. You will have to "
            "respond every 'turn' as the gameserver does not enforce any rules (much like "
            "a pyscial table doesn't enforce the rules of a card game "
            "We are currentlly developing this system every turn please respond with an "
            "card_move described as text, please try diffrent things out."
 
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
        # UI Control Booleans
        self.show_text_desc = False
        self.show_grid_ui = True

        self.fifo_dir = fifo_dir
        if test:
            self.players = [FIFOPlayer(i, fifo_dir) for i in range(1, player_count + 1)]
        else:
            self.players = [
                FIFOPlayer(1, fifo_dir),
                FIFOPlayer(2, fifo_dir),
                #LLMPlayer(2, fifo_dir),
                #LLMPlayer(3, fifo_dir),
                #LLMPlayer(4, fifo_dir),
            ]
        self.turn_number = 1
        
        # 1. Create the Table
        self.table = Table(seats=len(self.players))
        
        # Sync Table Seat names with Player names
        for i, player in enumerate(self.players): # TODO User PlayerId
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
        for p in self.players:
            p.send_turn(self.turn_number)
            p.send_table(self.table)

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
                    p = PlayerId.from_index(i)
                    action = parse_action(text, p)
                    if card_move:
                        print(f"{p} wants to {action}")
                        try:
                            # 4. Execute
                            if self.table.execute_card_move(action):
                                for player in self.players:
                                    player.send_card_move(f"{p}", action)

                        except ValueError as e:
                            self.players[i].send_message(f"Invalid move: {e}\n")
                
                self.turn_number += 1
        except KeyboardInterrupt:
            print("\nShutting down.")

if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
