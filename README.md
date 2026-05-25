# NeXa ToTem — Smart Desk Companion

NeXa ToTem is a planned premium smart desk companion. The goal is to build a small desk robot that sits on my desk, moves its head, shows emotions on a small screen, reads sensors, helps with study sessions, shows reminders, monitors the room, reacts with lights and sounds, and can be controlled by a wireless remote.

This project is currently in the planning and early build stage. The README describes the target product, planned hardware, and the build direction.

## Design Goal

NeXa ToTem should feel clean, useful, and premium. The style target is dark black and grey, with a simple Apple-like look, a rounded body, a moving head, a cute but modern screen face, soft RGB light, and no messy visible wires.

It is not meant to be a toy. The goal is to make a useful desk companion that can help with studying, reminders, room monitoring, and simple local controls.

## Target Product

The final goal is a complete working physical product with:

- Raspberry Pi brain
- Arduino hardware controller
- Moving head
- Screen face
- Camera
- Sensors
- RGB lights
- Speaker
- Wireless remote
- Inductive charging for the remote
- Local web panel
- Study mode
- Reminders
- Air monitoring
- Simple local system menu

## Planned Hardware

### Main Computer and Control

- Raspberry Pi 5 2GB
- Raspberry Pi 27W USB-C power supply
- 128GB microSD card
- Arduino Uno Rev3
- USB-A to USB-B cable for Arduino
- Adafruit 16-channel PWM / Servo Shield based on PCA9685
- Baguette S3 ESP32-S3 pre-soldered board
- NodeMCU ESP8266 for the remote controller

### Cooling and Power

- Argon THRML 30mm active cooler for Raspberry Pi 5
- Mean Well 5V 4A power supply for servos, RGB and 5V hardware
- Female DC jack screw terminal adapters
- 4700uF capacitors
- 74AHCT125 level shifter
- Resistor packs: 100K, 10K, 470 ohm
- SPDT slide switches

### Movement

- 2x TowerPro MG90D metal gear servos
- Pan and tilt neck mechanism
- Smooth head movement
- Head should stay light

### Display and Sound

- Small LCD / HDMI IPS display for the face and menu
- Mini external USB speaker
- Expressive emoji-style face
- Simple sounds for startup, buttons, warnings and notifications

### Camera and Sensors

- Raspberry Pi CSI camera module from the Waveshare 360-degree pan-tilt camera kit
- Adafruit VL53L4CX Time-of-Flight distance sensor
- BME680 / BME688 air and environment sensor
- LTR-329 light sensor
- CAP1188 capacitive touch sensor
- Sound sensor
- RFID RC522 module
- Grove ADS1115 4-channel 16-bit ADC
- Analog 2-axis thumb joystick
- Grove thumb joystick
- Colourful round tactile buttons

### Lighting

- Flexible RGB LED strip
- RGB diffuser parts planned for the 3D printed body
- RGB should show air quality, focus mode, warning, success, errors, idle state and notifications

### Remote Controller

- Wireless remote for controlling menu and system
- Joystick
- 3-4 buttons
- 1200mAh 3.7V LiPo battery
- PowerBoost 1000C charger / boost module
- Universal Qi wireless receiver module
- Universal Qi wireless transmitter module
- Rare earth magnets for side docking
- SPDT slide switch
- Optional vibration feedback
- Remote should dock magnetically to the side of NeXa ToTem
- Remote should charge wirelessly when docked
- Qi receiver must not charge the LiPo directly. It should feed the charger/boost circuit.

### Cables and Connection Parts

- STEMMA QT / Qwiic 100mm cables
- Grove 4-pin conversion cables
- Jumper wires
- Other small wiring parts as needed

## Physical Design

The body is planned as a modular 3D printed design. It should be easy to service and should keep the outside clean.

Planned printed parts:

- Head shell
- Neck mechanism
- Body shell
- Remote shell
- Side magnetic remote dock
- Bottom base
- RGB diffusers
- Internal mounting plates

Important design notes:

- Keep cable routing clean.
- Raspberry Pi must have airflow.
- Air sensor should not be placed next to heat.
- Head should contain only light parts: display, camera, distance sensor, shell and cables.
- Raspberry Pi, Arduino, speaker, PSU wiring and heavy parts should stay in the body.

## Planned Features

### 1. Home / Face Mode

- Shows expressive face
- Shows time and status
- Idle blinking
- Small emotional reactions

### 2. Air Monitor Mode

- Reads air and environment sensor data
- Shows temperature, humidity and air quality if available
- Uses RGB green, orange and red feedback
- Can warn the user to open a window

### 3. Study Mode

- Pomodoro timer
- Focus sessions
- Break sessions
- Sounds and RGB feedback
- Screen status

### 4. Reminder Mode

- Local reminders
- Reminder screen cards
- Sound notification
- RGB notification

### 5. Remote Control Mode

- Menu controlled by remote joystick and buttons
- Head movement control
- Mode selection
- Confirm, back, menu and action buttons
- Optional vibration feedback

### 6. Web Panel Mode

- Local web panel hosted on Raspberry Pi
- Phone or laptop control
- Sensor dashboard
- RGB control
- Head position control
- Reminder and study controls
- Local-first design with no cloud needed at the start

### 7. Sensor Mode

- Shows camera status
- Shows distance sensor status
- Shows air sensor status
- Shows light sensor status
- Shows touch sensor status
- Shows sound sensor status

### 8. System / Settings Mode

- Brightness
- Volume
- RGB brightness
- Movement speed
- Safe mode
- Hardware status
- Shutdown and restart options

## Menu Design

The menu should be simple, card-based and modern. The main menu is planned to include:

- Home
- Air
- Study
- Reminders
- Remote
- Lights
- Sensors
- Settings
- System

## Emotional Behaviour

NeXa ToTem should react using:

- LCD face expressions
- Small head movements
- RGB light
- Short sounds
- Remote vibration if added

Example states:

- Startup
- Ready
- Listening
- Thinking
- Happy
- Success
- Warning
- Error
- Study focus
- Break time
- Sleep
- Remote connected
- Air quality warning

## Planned Repository Layout

```text
docs/
system/
firmware/
tests/
scripts/
assets/
config/
```

- `docs/` contains product, hardware, mechanical and software notes.
- `system/` contains the Raspberry Pi runtime, LCD UI, local web panel, features, devices and services.
- `firmware/` contains Arduino Uno, ESP8266 remote and ESP32-S3 experiment firmware.
- `tests/` contains unit, integration, hardware, firmware, safety and smoke checks.
- `scripts/` contains setup, run, test, hardware and Git helper scripts.
- `assets/` contains UI files, icons, sounds and branding.
- `config/` contains example configuration files.

## Roadmap

1. Inventory and measurements
2. Electronics bench prototype
3. Software MVP
4. Mechanical prototype
5. Premium enclosure
6. Final integration
7. Polish and testing

## Current Status

NeXa ToTem is not finished yet. The current work is focused on planning the product, choosing the hardware, mapping the system design, and preparing the repository for the first real build steps.
