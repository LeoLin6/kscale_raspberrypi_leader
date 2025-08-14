#!/usr/bin/env python3

import socket
import json
import time
import asyncio
import signal
import sys
import os

# Add the current directory to Python path to import glove modules
sys.path.append('/home/dpsh/roh_demos/glove_ctrled_rohand')

from pykos import KOS
from pos_input_usb_glove import PosInputUsbGlove as PosInput

# UDP Configuration
UDP_HOST = "10.33.10.154"  # Target IP - change as needed
UDP_PORT = 8888
SEND_RATE = 10.0  # Hz - how often to send data

# Number of fingers from glove
NUM_FINGERS = 6

# Finger value processing
FINGER_MAX_VALUE = 65535  # Maximum finger sensor value

class CombinedGloveUDPSender:
    def __init__(self, udp_host=UDP_HOST, udp_port=UDP_PORT, send_rate=SEND_RATE):
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.send_rate = send_rate
        self.period = 1.0 / send_rate
        
        # Initialize components
        self.kos = None
        self.pos_input = None
        self.sock = None
        self.terminated = False
        
        # Setup signal handler
        signal.signal(signal.SIGINT, lambda signal, frame: self._signal_handler())
        
        # Last known finger data
        self.finger_data = [0 for _ in range(NUM_FINGERS)]

    def _signal_handler(self):
        print("\nYou pressed ctrl-c, stopping...")
        self.terminated = True

    async def setup_kos(self):
        """Setup KOS connection"""
        try:
            self.kos = KOS("127.0.0.1")
            print("✅ Connected to KOS service")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to KOS: {e}")
            return False

    async def setup_glove(self):
        """Setup glove connection"""
        try:
            self.pos_input = PosInput()
            if not await self.pos_input.start():
                print("❌ Failed to initialize glove")
                return False
            print("✅ Connected to USB glove")
            return True
        except Exception as e:
            print(f"❌ Failed to setup glove: {e}")
            return False

    def setup_udp(self):
        """Setup UDP socket"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"✅ UDP socket ready - sending to {self.udp_host}:{self.udp_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to setup UDP: {e}")
            return False

    async def get_motor_positions(self):
        """Get current motor positions from KOS"""
        motor_positions = {}
        try:
            resp = await self.kos.actuator.get_actuators_state()
            
            for state in resp.states:
                position = state.position
                
                # Invert positions for specific joint IDs (11, 15, 21, 25)
                if state.actuator_id in [11, 15, 21, 25]:
                    position = -position
                
                motor_positions[str(state.actuator_id)] = round(position, 1)
                
        except Exception as e:
            print(f"⚠️ Error getting motor positions: {e}")
            
        return motor_positions

    async def get_finger_positions(self):
        """Get current finger positions from glove"""
        try:
            raw_finger_data = await self.pos_input.get_position()
            
            # Flip finger values: max_value - current_value
            # This inverts the finger positions (FINGER_MAX_VALUE - value)
            flipped_finger_data = []
            for value in raw_finger_data:
                flipped_value = FINGER_MAX_VALUE - value
                flipped_finger_data.append(flipped_value)
            
            self.finger_data = flipped_finger_data
            
        except Exception as e:
            print(f"⚠️ Error getting finger positions: {e}")
            
        return self.finger_data

    async def send_combined_data(self):
        """Get both motor and finger data, then send via UDP"""
        try:
            # Get motor positions and finger data concurrently
            motor_positions, finger_data = await asyncio.gather(
                self.get_motor_positions(),
                self.get_finger_positions(),
                return_exceptions=True
            )
            
            # Handle any exceptions from the gather
            if isinstance(motor_positions, Exception):
                motor_positions = {}
            if isinstance(finger_data, Exception):
                finger_data = self.finger_data  # Use last known values
            
            # Build combined data packet
            combined_data = {
                "timestamp": time.time(),
                "joints": motor_positions,
                "fingers": finger_data
            }
            
            # Send via UDP
            json_data = json.dumps(combined_data)
            self.sock.sendto(json_data.encode('utf-8'), (self.udp_host, self.udp_port))
            
            # Print status
            motor_count = len(motor_positions)
            finger_count = len(finger_data)
            print(f"📡 Sent: {motor_count} motors, {finger_count} fingers at {time.strftime('%H:%M:%S')}")
            print(f"   Motors: {motor_positions}")
            print(f"   Fingers: {finger_data}")
            
        except Exception as e:
            print(f"❌ Error sending data: {e}")

    async def run(self):
        """Main run loop"""
        print("🤖 Starting Combined Glove + Motor UDP Sender...")
        
        # Setup all components
        if not await self.setup_kos():
            print("❌ KOS setup failed")
            return
            
        if not await self.setup_glove():
            print("❌ Glove setup failed")
            return
            
        if not self.setup_udp():
            print("❌ UDP setup failed")
            return
        
        print(f"✅ All systems ready! Sending data at {self.send_rate} Hz")
        print("   Press Ctrl+C to stop")
        
        try:
            while not self.terminated:
                await self.send_combined_data()
                await asyncio.sleep(self.period)
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        
        if self.pos_input:
            try:
                await self.pos_input.stop()
                print("✅ Glove connection closed")
            except:
                pass
                
        if self.sock:
            try:
                self.sock.close()
                print("✅ UDP socket closed")
            except:
                pass
                
        print("✅ Cleanup complete")

# Test mode function
async def test_single_send():
    """Send a single packet for testing"""
    sender = CombinedGloveUDPSender()
    
    print("🧪 Test mode: sending single combined packet...")
    
    if not await sender.setup_kos():
        print("❌ KOS setup failed for test")
        return
        
    if not await sender.setup_glove():
        print("❌ Glove setup failed for test")
        return
        
    if not sender.setup_udp():
        print("❌ UDP setup failed for test")
        return
    
    # Send one packet
    await sender.send_combined_data()
    
    # Cleanup
    await sender.cleanup()
    print("🧪 Test complete")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode - send single packet
        asyncio.run(test_single_send())
    else:
        # Continuous mode
        sender = CombinedGloveUDPSender()
        asyncio.run(sender.run()) 