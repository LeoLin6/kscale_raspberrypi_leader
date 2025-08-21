#!/bin/bash

# Check for existing KOS process
if pgrep -x "kos" > /dev/null; then
    echo "❌ KOS is already running. Please stop it first:"
    echo "   kill $(pgrep -x kos)"
    exit 1
fi

# Source conda and start KOS service
source ~/miniforge3/etc/profile.d/conda.sh
conda activate kos

# Start KOS service in background
kos service &
KOS_PID=$!

# Wait for KOS to be ready
sleep 5

# Create new tmux session for torque disable and keep it running
tmux kill-session -t kos-torque 2>/dev/null  # Clean up any existing session
tmux new-session -d -s kos-torque "bash -c 'source ~/miniforge3/etc/profile.d/conda.sh && conda activate kos && kos actuator torque disable all && echo \"Torque disabled. Session kept alive.\" && while true; do sleep 30; done'"

# Verify torque status
sleep 2
if ! tmux has-session -t kos-torque 2>/dev/null; then
    echo "❌ Failed to create torque control session"
    kill $KOS_PID  # Clean up KOS service if torque session fails
    exit 1
fi

echo "✅ KOS service started (PID: $KOS_PID)"
echo "✅ Torque disabled in tmux session 'kos-torque'"
echo ""
echo "To view torque session: tmux attach -t kos-torque"
echo "To detach from session: Ctrl+B, then D"
echo "To stop KOS: kill $KOS_PID"
echo ""
echo "▶️ Launching combined glove + motor UDP sender..."
python3 /home/dpsh/kscale_raspberrypi_leader/combined_glove_udp_sender.py