#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:$PATH"
sshpass -p 'bob' ssh -o StrictHostKeyChecking=no gil@192.168.0.27 \
  "echo 'bob' | sudo -S git -C /opt/sepsis-dx pull origin main 2>&1 && \
   echo 'bob' | sudo -S systemctl restart sepsis-dx 2>&1"

echo "Done."
