import asyncio
import os

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
                os.write(self.fd_out, f"{message}\n".encode())
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
        self.players = [Player(i, fifo_dir) for i in range(1, player_count + 1)]
        self.turn_number = 1

    async def run_game(self):
        for player in self.players:
            player.connect()
        
        try:
            while True:
                # 1. Announce Turn
                for p in self.players:
                    p.send_message(f"\n--- TURN {self.turn_number} ---")
                    if self.turn_number > 1:
                        for other in self.players:
                            p.send_message(f"{other.name} said: {other.last_input}")
                    p.send_message("Type your move and press Enter:")

                print(f"Server: Waiting for all {len(self.players)} players...")

                # 2. WAIT FOR ALL (This is the blocking part)
                # We use asyncio.gather to wait for every player's poll to return
                results = await asyncio.gather(*(p.wait_for_input() for p in self.players))
                
                print(f"Server: All inputs received: {results}")
                self.turn_number += 1
                
        except KeyboardInterrupt:
            print("\nShutting down.")

if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.run_game())
