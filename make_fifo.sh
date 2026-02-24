# Define the directory and number of players
FIFO_DIR="fifo"
PLAYER_COUNT=4

# Create the directory if it doesn't exist
if [ ! -d "$FIFO_DIR" ]; then
    mkdir "$FIFO_DIR"
    echo "Created directory: $FIFO_DIR"
fi

# Loop to create p1_in, p1_out, p2_in, etc.
for i in $(seq 1 $PLAYER_COUNT); do
    IN_PIPE="$FIFO_DIR/p${i}_in"
    OUT_PIPE="$FIFO_DIR/p${i}_out"

    # Create the 'in' pipe if it doesn't exist
    [ -p "$IN_PIPE" ] || mkfifo "$IN_PIPE"
    
    # Create the 'out' pipe if it doesn't exist
    [ -p "$OUT_PIPE" ] || mkfifo "$OUT_PIPE"

    echo "Initialized pipes for Player $i: $IN_PIPE, $OUT_PIPE"
done

echo "Done. FIFOs are ready for the Python coordinator."
