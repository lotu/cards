#!/bin/bash

cd fifo

tmux new-session  \; \
    split-window -v -p 30 \; \
    select-pane -t 1 \; \
    split-window -h \; \
    split-window -h \; \
    select-pane -t 1 \; \
    split-window -h \; \
    select-pane -t 5 \; \
    split-window -h \; \
    split-window -h \; \
    select-pane -t 5 \; \
    split-window -h \; \
    select-pane -t 1 \; \
    send-keys -t 1 "cat p1_out" Enter \; \
    send-keys -t 2 "cat p2_out" Enter \; \
    send-keys -t 3 "cat p3_out" Enter \; \
    send-keys -t 4 "cat p4_out" Enter \; \
    send-keys -t 5 "cat > p1_in" Enter \; \
    send-keys -t 6 "cat > p2_in" Enter \; \
    send-keys -t 7 "cat > p3_in" Enter \; \
    send-keys -t 8 "cat > p4_in" Enter \; \
