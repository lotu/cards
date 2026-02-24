import asyncio
import os
from cards import Table, table_to_str, describe_table
from enums import Card

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
        
        output_parts.append(f"\n--- TURN {self.turn_number} ---\n")
        
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
                
                # 4. Wait for all players to send a line (ignoring the content for now)
                await asyncio.gather(*(p.wait_for_input() for p in self.players))
                
                self.turn_number += 1
        except KeyboardInterrupt:
            print("\nShutting down.")

if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
