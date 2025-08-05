#!/usr/bin/env python3
"""UDP sender to broadcast joint angles from Raspberry Pi."""

import asyncio
import json
import sys
import socket
from datetime import datetime

# Add pykos-puppeteer to path
sys.path.insert(0, '/home/dpsh/pykos-puppeteer')

from pykos_puppeteer.source import CheapoPuppeteer

class JointUDPSender:
    def __init__(self, host="0.0.0.0", port=8888):
        self.host = host
        self.port = port
        self.puppeteer = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Optimize socket for low latency (removed problematic option)
        
    async def setup_puppeteer(self):
        """Setup connection to KOS service."""
        try:
            self.puppeteer = CheapoPuppeteer(
                ip="192.168.10.1",
                actuator_ids=[11, 12, 13, 14, 15, 21, 22, 23, 24, 25],
                inverted_ids=[11, 15, 21, 25],
            )
            print(f"Connected to KOS service on 192.168.10.1")
            return True
        except Exception as e:
            print(f"Failed to connect to KOS: {e}")
            return False
    
    async def get_joint_data(self):
        """Get current joint positions."""
        if not self.puppeteer:
            return None
        
        try:
            pose = await self.puppeteer.get_target_pose()
            return {
                "timestamp": datetime.now().isoformat(),
                "joints": pose,
                "count": len(pose),
                "source": "puppeteer"
            }
        except Exception as e:
            return None  # Don't print errors to reduce lag
    
    async def broadcast_joint_data(self):
        """Broadcast joint data via UDP."""
        if not await self.setup_puppeteer():
            print("Failed to setup puppeteer. Exiting.")
            return
        
        print(f"Starting UDP broadcast on {self.host}:{self.port}")
        print("Broadcasting to network...")
        print("Press Ctrl+C to stop")
        
        # Pre-encode broadcast address - use direct IP for better reliability
        broadcast_addr = ('192.168.10.36', self.port)  # Your Mac's actual IP
        
        while True:
            try:
                joint_data = await self.get_joint_data()
                if joint_data:
                    # Convert to JSON and send (minimal processing)
                    message = json.dumps(joint_data).encode('utf-8')
                    self.sock.sendto(message, broadcast_addr)
                
                # Faster update rate for lower latency
                await asyncio.sleep(0.01)  # 100Hz for lower latency
                
            except KeyboardInterrupt:
                print("\nStopping UDP broadcast...")
                break
            except Exception as e:
                # Minimal error handling to reduce lag
                await asyncio.sleep(0.1)

if __name__ == "__main__":
    sender = JointUDPSender()
    try:
        asyncio.run(sender.broadcast_joint_data())
    except KeyboardInterrupt:
        print("\nShutting down...") 