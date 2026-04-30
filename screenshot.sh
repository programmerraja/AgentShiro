#!/bin/bash

SAVE_DIR="$HOME/screenshots"
INTERVAL=30
IDLE_THRESHOLD=60000   # 60 sec (in ms)

mkdir -p "$SAVE_DIR"

paused=0

# Toggle pause with SIGUSR1
toggle_pause() {
    if [ $paused -eq 0 ]; then
        paused=1
        echo "Paused"
    else
        paused=0
        echo "Resumed"
    fi
}

trap toggle_pause SIGUSR1

while true; do
    if [ $paused -eq 0 ]; then
        idle_time=$(xprintidle)

        if [ "$idle_time" -lt "$IDLE_THRESHOLD" ]; then
            timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
            scrot -z "$SAVE_DIR/screenshot_$timestamp.png"
        fi
    fi

    sleep $INTERVAL
done

# PID_FILE="/tmp/screenshot_pid"; SCRIPT="$HOME/Documents/Personal Code/AgentShiro/screenshot.sh"; if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then kill $(cat "$PID_FILE") && rm -f "$PID_FILE" && notify-send "Screenshot" "Stopped"; else nohup "$SCRIPT" > /dev/null 2>&1 & echo $! > "$PID_FILE" && notify-send "Screenshot" "Started"; fi