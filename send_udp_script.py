#!/usr/bin/env python3

import socket
import json
import time
import asyncio
from pykos import KOS

# UDP Configuration
UDP_HOST = "192.168.42.167"  # localhost - change this to target IP if needed
UDP_PORT = 8888
SEND_RATE = 10.0  # Hz - how often to send motor positions

async def send_motor_positions_udp():
    """Continuously read motor positions and send them via UDP"""
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Connect to KOS service
        kos = KOS("127.0.0.1")
        print(f"Sending motor positions to {UDP_HOST}:{UDP_PORT} at {SEND_RATE} Hz")
        print("Press Ctrl+C to stop...")
        
        period = 1.0 / SEND_RATE
        
        while True:
            try:
                # Get all actuator states
                resp = await kos.actuator.get_actuators_state()
                
                # Build data packet in the format expected by your receiver
                motor_data = {
                    "timestamp": time.time(),
                    "joints": {}
                }
                
                for state in resp.states:
                    # Convert to the format your receiver expects: "joint_id": position
                    position = state.position
                    
                    # Invert positions for specific joint IDs (11, 15, 21, 25)
                    if state.actuator_id in [11, 15, 21, 25]:
                        position = -position
                    
                    motor_data["joints"][str(state.actuator_id)] = round(position, 2)
                
                # Convert to JSON and send via UDP
                json_data = json.dumps(motor_data)
                sock.sendto(json_data.encode('utf-8'), (UDP_HOST, UDP_PORT))
                
                # Print status (optional - comment out for less output)
                joint_count = len(motor_data["joints"])
                print(f"Sent data for {joint_count} joints at {time.strftime('%H:%M:%S')}: {motor_data['joints']}")
                
            except Exception as e:
                print(f"Error getting motor data: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(period)
            
    except KeyboardInterrupt:
        print("\nStopping UDP transmission...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
        print("UDP socket closed.")

async def test_single_send():
    """Send a single packet for testing"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        kos = KOS("127.0.0.1")
        resp = await kos.actuator.get_actuators_state()
        
        motor_data = {
            "timestamp": time.time(),
            "joints": {}
        }
        
        for state in resp.states:
            position = state.position
            
            # Invert positions for specific joint IDs (11, 15, 21, 25)
            if state.actuator_id in [11, 15, 21, 25]:
                position = -position
            
            motor_data["joints"][str(state.actuator_id)] = round(position, 2)
        
        json_data = json.dumps(motor_data, indent=2)
        print("Sending data:")
        print(json_data)
        
        sock.sendto(json_data.encode('utf-8'), (UDP_HOST, UDP_PORT))
        print(f"Data sent to {UDP_HOST}:{UDP_PORT}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode - send single packet
        print("Test mode: sending single UDP packet...")
        asyncio.run(test_single_send())
    else:
        # Continuous mode
        asyncio.run(send_motor_positions_udp()) 