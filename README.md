# ros2_ackermann_motor_ctrl

A ROS 2 motor control package for Ackermann steering platforms, bridging a ROS 2 Python node with an Arduino Mega 2560 over USB serial. The system supports both **autonomous (ROS) control** and **manual RC override** via an FS-i6 transmitter and IBUS receiver.

---

## Table of Contents

- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [System Architecture](#system-architecture)
- [Wiring & Circuitry](#wiring--circuitry)
- [Installation](#installation)
  - [1. ROS 2 Package Setup](#1-ros-2-package-setup)
  - [2. Python Serial Library](#2-python-serial-library)
  - [3. Arduino Setup](#3-arduino-setup)
  - [4. Serial Port Permissions (Linux)](#4-serial-port-permissions-linux)
- [Running the System](#running-the-system)
- [ROS 2 Interface](#ros-2-interface)
- [Serial Command Protocol](#serial-command-protocol)
- [Mode Switching (RC vs ROS)](#mode-switching-rc-vs-ros)
- [Watchdog Safety](#watchdog-safety)
- [References](#references)

---

## Overview

This package implements a hybrid drive-train control system for a ROS 2-based autonomous vehicle with Ackermann steering. It consists of:

- A **ROS 2 Python node** (`arduino_motor`) that subscribes to motor commands and relays them over USB serial.
- An **Arduino Mega 2560** sketch that reads serial commands and controls a DC motor via a BTS7960 motor driver and two servos for steering.
- An **IBUS RC receiver** (FS-i6) enabling real-time mode switching between manual and autonomous control.

---

## Hardware Requirements

| Component | Details |
|---|---|
| Microcontroller | Arduino Mega 2560 |
| Motor Driver | BTS7960 (high-current H-bridge) |
| RC Transmitter/Receiver | FS-i6 with IBUS receiver |
| Servos | 2× servo motors (steering) |
| Computing Platform | Any Linux machine running ROS 2 |
| Power | External battery + buck converter for servo 5V rail |

---

## System Architecture

```
ROS 2 Node  →  /motor_command (std_msgs/String)
                        ↓
              Serial USB @ 115200 baud
                        ↓
               Arduino Mega 2560
               ┌──────────────────┐
               │  BTS7960 Driver  │ → DC Motor
               │  Servo1 (D8)     │ → Steering Servo 1
               │  Servo2 (D9)     │ → Steering Servo 2
               │  IBUS (Serial1)  │ ← FS-i6 RC Receiver
               └──────────────────┘
```

The ROS node acts as a transparent serial bridge. All control logic (PWM generation, watchdog, mode switching) runs on the Arduino.

---

## Wiring & Circuitry

### Motor Driver → Arduino

| BTS7960 Pin | Arduino Pin |
|---|---|
| RPWM | D6 |
| LPWM | D7 |
| R_EN | D4 |
| L_EN | D5 |
| VCC | 5V |
| GND | GND |

### Motor Driver → Power

| BTS7960 Pin | Connect To |
|---|---|
| B+ / VCC (motor power) | Battery + |
| B- / GND | Battery − |
| Motor terminals | DC Motor |

### Servo → Arduino

| Servo Wire | Arduino Pin |
|---|---|
| Signal (Servo 1) | D8 |
| Signal (Servo 2) | D9 |
| VCC | 5V (via buck converter) |
| GND | GND |

### FS-i6 Channel Mapping

| Channel | Function |
|---|---|
| CH1 | Servo 2 (steering) |
| CH2 | Direction (forward / back) |
| CH3 | Speed (throttle) |
| CH4 | Servo 1 |
| CH5 | Mode switch (RC ↔ ROS) |

> **Note:** The IBUS receiver's signal wire connects to Arduino `Serial1` (pins TX1/RX1).

<img width="3938" height="4070" alt="image" src="https://github.com/user-attachments/assets/2ce60f97-c852-4d4e-b5af-94eb3ef74e89" />


---

## Installation

### Prerequisites

- Ubuntu 22.04 or later
- ROS 2 Humble (or newer) installed and sourced
- Arduino IDE 2.x installed
- Arduino Mega 2560 connected via USB

---

### 1. ROS 2 Package Setup

**Step 1 — Create a workspace (skip if you already have one):**

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

**Step 2 — Clone this repository:**

```bash
git clone https://github.com/hermanumrao/ros2_ackermann_motor_ctrl.git
```

**Step 3 — Install ROS dependencies:**

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

**Step 4 — Build the workspace:**

```bash
colcon build
```

**Step 5 — Source the workspace:**

```bash
source install/setup.bash
```

Add to your `~/.bashrc` to auto-source on every terminal:

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

### 2. Python Serial Library

The ROS node requires `pyserial` to communicate over USB serial.

```bash
pip3 install pyserial
```

Verify the installation:

```bash
python3 -c "import serial; print(serial.__version__)"
```

---

### 3. Arduino Setup

#### 3.1 Install Required Libraries

Open Arduino IDE, then go to **Sketch → Include Library → Manage Libraries** and install:

- **IBusBM** — for IBUS RC receiver communication
- **Servo** — for servo control (usually pre-installed)

#### 3.2 Identify the Serial Port

Connect the Arduino Mega via USB and find its port:

```bash
ls /dev/ttyUSB*
# or
ls /dev/ttyACM*
```

Typically it appears as `/dev/ttyUSB0` or `/dev/ttyACM0`.

#### 3.3 Upload the Arduino Sketch

1. Open Arduino IDE.
2. Go to **File → Open** and select the sketch from the `arduino_codes/` folder in this repo.
3. Set the board: **Tools → Board → Arduino Mega or Mega 2560**
4. Set the processor: **Tools → Processor → ATmega2560**
5. Set the port: **Tools → Port → /dev/ttyUSB0** (or your detected port)
6. Click **Upload** (→).

#### 3.4 Verify Arduino is Running

Open the Serial Monitor (**Tools → Serial Monitor**) and set baud rate to **115200**. You should see:

```
BTS7960 + Servo + RC/ROS Switch Ready
```

---

### 4. Serial Port Permissions (Linux)

If you encounter a `Permission denied` error when accessing `/dev/ttyUSB0`, add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

Then **log out and log back in** (or reboot) for the change to take effect.

---

## Running the System

**Terminal 1 — Launch the ROS 2 motor node:**

```bash
ros2 run arduino_motor motor_node
```

The node will open the serial connection to the Arduino and start listening on the `/motor_command` topic.

> If the serial port is different from the default, check the node's source or parameters and update accordingly.

**Terminal 2 — Send test commands:**

```bash
# Drive forward at speed 150
ros2 topic pub /motor_command std_msgs/msg/String "{data: 'F150'}"

# Drive reverse at speed 200
ros2 topic pub /motor_command std_msgs/msg/String "{data: 'B200'}"

# Stop
ros2 topic pub /motor_command std_msgs/msg/String "{data: 'STOP'}"

# Steer: Servo 1 to 90°
ros2 topic pub /motor_command std_msgs/msg/String "{data: 'SERVO190'}"

# Steer: Servo 2 to 45°
ros2 topic pub /motor_command std_msgs/msg/String "{data: 'SERVO245'}"
```

---

## ROS 2 Interface

| Property | Value |
|---|---|
| Topic | `/motor_command` |
| Message Type | `std_msgs/msg/String` |
| Direction | ROS → Arduino (one-way) |

The node receives a string command, converts it to uppercase, and writes it directly to the Arduino over serial. There is no feedback from the Arduino back to ROS.

---

## Serial Command Protocol

### Motor Commands

| Command | Description | Example |
|---|---|---|
| `F<speed>` | Drive forward | `F150` |
| `B<speed>` | Drive reverse | `B200` |
| `STOP` | Stop motor | `STOP` |

Speed range: `0` – `255`

### Servo Commands

| Command | Description | Example |
|---|---|---|
| `SERVO1<angle>` | Set Servo 1 angle | `SERVO190` |
| `SERVO2<angle>` | Set Servo 2 angle | `SERVO245` |

Angle range: `0` – `180`

### System Commands

| Command | Description |
|---|---|
| `HEARTBEAT` | Keep-alive ping (resets watchdog) |

---

## Mode Switching (RC vs ROS)

The mode is determined by **Channel 5** of the FS-i6 transmitter:

| CH5 Value | Active Mode |
|---|---|
| ≤ 1500 | **RC Mode** — direct manual control via transmitter |
| > 1500 | **ROS Mode** — autonomous control via serial commands |

In **RC Mode**, the Arduino reads IBUS channels directly to drive the motor and servos — the ROS node has no effect.

In **ROS Mode**, the Arduino executes commands received over USB serial from the ROS node.

---

## Watchdog Safety

The Arduino implements a software watchdog timer:

- **Timeout:** 1000 ms
- If no valid ROS command is received within 1 second, the motor is automatically stopped.
- This prevents runaway behaviour if the ROS node crashes or the serial connection is lost.

Always send a `HEARTBEAT` command if your control loop is slow to prevent unintended stops.

---

## References

- [Circuitry & Wiring Diagram](https://github.com/hermanumrao/Autnomous-nav-DOCS/blob/main/hardware/drive-train/electronics/circuitry.md)
- [Arduino Motor Control Package — Full Algorithm Docs](https://github.com/hermanumrao/Autnomous-nav-DOCS/blob/main/algorithms/Arduino_motor_control%20package.md)
- [Autonomous Navigation Project Docs](https://github.com/hermanumrao/Autnomous-nav-DOCS)
