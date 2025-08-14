# KScale Raspberry Pi Leader Arm Bimanual Configuration

A comprehensive system for controlling bimanual robotic arms using **KOS-ZBot** actuators and **OyMotion** data gloves via UDP communication.

## Overview

This repository contains scripts for creating a leader-follower robotic control system where:
- **Leader arm**: Controlled by OyMotion data gloves and KOS actuator positions
- **Follower arm**: Receives UDP commands to mirror leader movements
- **Bimanual coordination**: Simultaneous control of both arms with finger tracking

## To actually teleoperate

**IMPORTANT**: Always disable motor torque to control the leader arms:

```bash
# disable all motor torque
kos actuator torque disable all

# Check motor positions safely
kos status
```

## System Components

### Hardware
- **KScale Robotics ZBot** - Humanoid robot with actuator-controlled joints
- **OyMotion Data Glove** - USB/BLE glove for finger position sensing
- **Raspberry Pi** - Running the leader arm control system
- **Network connection** - UDP communication between leader and follower

### Software Stack
- **[KOS (K-Scale Operating System)](https://github.com/kscalelabs/kos)** - Robot control framework
- **[PyKOS](https://github.com/kscalelabs/pykos)** - Python interface for KOS
- **OyMotion SDK** - Glove data acquisition
- **UDP networking** - Real-time data transmission

## Scripts Description

### 1. `get_motor_pos.py`
Basic script to read current motor positions from KOS service.

```bash
python3 get_motor_pos.py
```

**Output:**
```
Actuator 11: 45.23° at -12.34°/s
Actuator 12: 30.15° at 5.67°/s
...
```

### 2. `send_udp_script.py`
Sends motor positions via UDP in the format expected by follower robots.

```bash
# Continuous sending
python3 send_udp_script.py

# Test single packet
python3 send_udp_script.py test
```

**Features:**
- 10 Hz update rate (configurable)
- Auto-inverts joints 11, 15, 21, 25 for proper mirroring
- JSON format compatible with robot control systems

**Output format:**
```json
{
  "timestamp": 1703123456.789,
  "joints": {
    "11": -45.2,  // left_shoulder_pitch (inverted)
    "12": 30.1,   // left_shoulder_roll
    "13": 15.3,   // left_shoulder_yaw
    "14": 60.0,   // left_elbow
    "15": -0.5,   // left_wrist (inverted)
    "21": 45.2,   // right_shoulder_pitch (inverted)
    "22": -30.1,  // right_shoulder_roll
    "23": -15.3,  // right_shoulder_yaw
    "24": -60.0,  // right_elbow
    "25": 0.5     // right_wrist (inverted)
  }
}
```

### 3. `combined_glove_udp_sender.py` ⭐ **Main Script**
The primary script that combines both robot motor positions and glove finger data.

```bash
# Continuous operation
python3 combined_glove_udp_sender.py

# Test mode
python3 combined_glove_udp_sender.py test
```

**Features:**
- **Dual data streams**: Robot joints + glove fingers
- **Real-time operation**: 10 Hz update rate
- **Error resilience**: Continues operation if one source fails
- **Complete telemetry**: Timestamps, joint positions, finger positions

**Output format:**
```json
{
  "timestamp": 1703123456.789,
  "joints": {
    "11": 45.0,   // left_shoulder_pitch
    "12": 30.0,   // left_shoulder_roll
    "13": 15.0,   // left_shoulder_yaw
    "14": 60.0,   // left_elbow
    "15": 0.0,    // left_wrist
    "21": -45.0,  // right_shoulder_pitch
    "22": -30.0,  // right_shoulder_roll
    "23": -15.0,  // right_shoulder_yaw
    "24": -60.0,  // right_elbow
    "25": 0.0     // right_wrist
  },
  "fingers": [
    32768,  // thumb raw value (0-65535)
    40000,  // index finger raw value
    25000,  // middle finger raw value
    30000,  // ring finger raw value
    20000,  // pinky raw value
    35000   // 6th finger/sensor raw value
  ]
}
```

### 4. `glove_ctrled_hand_modified.py`
Modified version of OyMotion's glove control script with hand control disabled.

```bash
python3 glove_ctrled_hand_modified.py
```

**Features:**
- **Glove-only mode**: Hand control commented out
- **USB glove support**: Configured for USB connection
- **Data logging**: Prints finger positions to console

### 5. `joint_udp_sender.py`
Original joint UDP sender script for basic joint position transmission.

## Joint Mapping

The system uses the following joint ID mapping for bimanual control:

| Joint ID | Joint Name | Description | Inverted |
|----------|------------|-------------|----------|
| 11 | `left_shoulder_pitch` | Left arm forward/back | ✅ |
| 12 | `left_shoulder_roll` | Left arm side-to-side | ❌ |
| 13 | `left_shoulder_yaw` | Left arm twist | ❌ |
| 14 | `left_elbow` | Left elbow bend | ❌ |
| 15 | `left_wrist` | Left wrist rotation | ✅ |
| 21 | `right_shoulder_pitch` | Right arm forward/back | ✅ |
| 22 | `right_shoulder_roll` | Right arm side-to-side | ❌ |
| 23 | `right_shoulder_yaw` | Right arm twist | ❌ |
| 24 | `right_elbow` | Right elbow bend | ❌ |
| 25 | `right_wrist` | Right wrist rotation | ✅ |

## Installation & Setup

### Prerequisites

1. **KOS Service Running**:
   ```bash
   # Start KOS service
   kos service
   ```

2. **Python Dependencies**:
   ```bash
   pip install pykos asyncio
   ```

3. **OyMotion Glove Setup**:
   - Connect USB glove to Raspberry Pi
   - Install OyMotion dependencies from their repo
   - Verify glove detection: `lsusb`

### Network Configuration

Update the UDP target IP in scripts:
```python
UDP_HOST = "192.168.42.167"  # Change to your follower robot IP
UDP_PORT = 8888
```

### Running the System

1. **Start KOS service** on robot:
   ```bash
   kos service
   ```

2. **Safety: Disable torque** (emergency stop):
   ```bash
   # Disable torque on all motors for safety
   kos actuator torque disable all
   
   # To re-enable when ready:
   kos actuator torque enable all
   ```

3. **Check system status**:
   ```bash
   # View real-time actuator positions and status
   kos status
   ```

4. **Connect glove** and verify:
   ```bash
   python3 glove_ctrled_hand_modified.py
   ```

5. **Start combined telemetry**:
   ```bash
   python3 combined_glove_udp_sender.py
   ```

## Troubleshooting

### Common Issues

**KOS Connection Failed**:
- Ensure KOS service is running: `kos service`
- Check KOS is accessible: `kos status`
- Verify actuator communication: `kos actuator dump all`
- Check torque status: `kos actuator torque disable all` (for safety)

**Glove Not Detected**:
- Check USB connection: `lsusb`
- Verify permissions: `ls -l /dev/ttyUSB*`
- Try BLE mode if USB fails

**UDP Transmission Issues**:
- Verify network connectivity: `ping 192.168.42.167`
- Check firewall settings
- Confirm port 8888 is open

**Joint Inversion Problems**:
- Joints 11, 15, 21, 25 are automatically inverted
- Modify inversion list in script if needed

### Performance Tuning

**Adjust Update Rate**:
```python
SEND_RATE = 10.0  # Hz - increase for faster updates
```

**Network Buffer Size**:
```python
sock.recvfrom(4096)  # Increase if data is large
```

## Integration Examples

### Follower Robot Receiver

Example receiver script for follower robot:
```python
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 8888))

while True:
    data, addr = sock.recvfrom(4096)
    robot_data = json.loads(data.decode('utf-8'))
    
    joints = robot_data["joints"]
    fingers = robot_data["fingers"]
    
    # Control follower robot with received data
    control_robot(joints, fingers)
```

### ROS Integration

For ROS systems, convert to ROS messages:
```python
from sensor_msgs.msg import JointState

def convert_to_ros_joints(joints_dict):
    joint_state = JointState()
    joint_state.header.stamp = rospy.Time.now()
    
    for joint_id, position in joints_dict.items():
        joint_state.name.append(f"joint_{joint_id}")
        joint_state.position.append(math.radians(position))
    
    return joint_state
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Create Pull Request

## License

This project is part of the KScale ecosystem. See individual component licenses for details.

## Related Projects

- **[KOS](https://github.com/kscalelabs/kos)** - K-Scale Operating System
- **[KOS-ZBot](https://github.com/kscalelabs/kos-zbot)** - ZBot robot control
- **[OyMotion ROH Demos](https://github.com/oymotion/roh_demos)** - Original glove control demos

## Support

For issues and questions:
- **KOS-related**: [KScale Labs Issues](https://github.com/kscalelabs/kos/issues)
- **Glove-related**: [OyMotion Support](https://github.com/oymotion/roh_demos/issues)
- **This repository**: [Create an issue](https://github.com/LeoLin6/kscale_raspberrypi_leader/issues)

---

**Built with ❤️ for the robotics community**
