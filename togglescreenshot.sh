#!/bin/bash

PID_FILE="/tmp/screenshot_pid";
SCRIPT="$HOME/Documents/Personal Code/AgentShiro/screenshot.sh";
if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1;
then kill $(cat "$PID_FILE") && rm -f "$PID_FILE" && notify-send "Screenshot" "Stopped";
else nohup "$SCRIPT" > /dev/null 2>&1 & echo $! > "$PID_FILE" && notify-send "Screenshot" "Started";
fi