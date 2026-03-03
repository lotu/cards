import asyncio
import os
import re
from cards import Table, table_to_str, describe_table
from enums import *
from parse import parse_card

class Player:
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

class GameServer:
    def __init__(self, player_count=4, fifo_dir="fifo"):
        # UI Control Booleans
        self.show_text_desc = False
        self.show_grid_ui = True

        self.fifo_dir = fifo_dir
        self.players = [Player(i, fifo_dir) for i in range(1, player_count + 1)]
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

                # Interpret each player's input
                for i, text in enumerate(inputs):
                    action = interpret_input(text, i, self.table)
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


def interpret_input(text: str, player_idx: int, table: Table) -> Optional[Action]:
    """
    Parses player input into a structured Action object.
    Does NOT modify the game state.
    """
    s = text.lower().strip()
    if not s:
        return None

    # The target for a draw is always that player's hand
    target_loc = Location.from_seat(player_idx + 1, SeatPart.HAND)

    # 1. Check for a specific card name (e.g., "Ace of Spades" from discard)
    if len(table.discard) > 0:
        try:
            target_card = parse_card(s)
            # If they named the top card of the discard pile
            if target_card == table.discard[-1]:
                return Action(
                    source=Location.DISCARD,
                    target=target_loc,
                    cards=target_card
                )
        except ValueError:
            pass # Not a card name, continue to general draw logic

    # 2. Check for general "Draw" keywords
    draw_keywords = ["draw", "take", "get", "pick", "hit"]
    if any(k in s for k in draw_keywords):
        print(s)
        # Determine quantity
        count_match = re.search(r'\d+', s)
        count = int(count_match.group()) if count_match else 1

        # Determine source (default to Stack)
        from_discard = "discard" in s or "pile" in s
        source_loc = Location.DISCARD if from_discard else Location.STACK

        return Action(source=source_loc, target=target_loc, count=count)

    return None


if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
