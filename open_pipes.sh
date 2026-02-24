#!/bin/bash
FIFO_DIR="fifo"
PLAYER_COUNT=4

mkdir -p "$FIFO_DIR"
# THE TRICK: Open the pipes for writing in the background.
# This keeps a 'writer' active so 'cat' doesn't close when Python stops.
# Previous tirck that works in the shell but not a script 
# exec 3<> creates a new output for the bash shell echo 'ls -l' >&3
sleep 8h > "$FIFO_DIR/p1_out" &
#sleep 8h > "$FIFO_DIR/p1_in" &
sleep 8h > "$FIFO_DIR/p2_out" &
#sleep 8h > "$FIFO_DIR/p2_in" &
sleep 8h > "$FIFO_DIR/p3_out" &
#sleep 8h > "$FIFO_DIR/p3_in" &
sleep 8h > "$FIFO_DIR/p4_out" &
#sleep 8h > "$FIFO_DIR/p4_in" &


echo "FIFOs are locked open. You can now start/stop the Python script freely."
