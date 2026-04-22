# Marathon -- Breadboard Prototype Build Guide

This document covers the complete process of building the breadboard prototype for the Marathon handheld. It was built over two sessions (2026-04-03 and 2026-04-04) and validates all major subsystems before moving to custom PCB design.

The prototype uses breakout board modules on a breadboard. The final build will integrate all ICs (IP5306, PCM5102A, PAM8403) as bare chips on a custom PCB, to be assembled by JLCPCB.

---

## Prerequisites

### Hardware Needed

| Component | Notes |
|-----------|-------|
| Raspberry Pi Zero 2 W | Solder header pins or buy WH with pre-soldered header pins |
| IP5306 breakout board | Mine had no USB port. Pads: OUT-5V, GND, BAT, GND, GND, VIN |
| ILI9341 3.2" SPI display breakout | 14-pin module (9 used, 5 touch pins unused) |
| PCM5102A DAC breakout | 11-pin left side + 3-pin right side (R, G, L audio outputs) |
| PAM8403 amplifier breakout | 9 pins: ROUT-, ROUT+, LOUT+, LOUT-, POWER-, POWER+, L, G, R |
| 3.7V LiPo battery | 500mAh for prototype (any small LiPo works) |
| 2x small speakers | 8 ohm, 1W, pre-wired |
| Tactile push buttons | From any kit or button pack |
| Breadboard | Standard full-size |
| Jumper wires | M-M, M-F, F-F (I had to make F-F from M-M, see below) |
| 22 AWG solid core wire | For soldering to breakout boards |
| USB cable (donor) | My breakout had no port, used for powering the IP5306's VIN pad |
| SD card | With RetroPie flashed |
| Soldering iron + solder | For connecting wires to breakout boards |
| Multimeter | For verifying voltages and continuity |
| Heat shrink tubing | Optional, for insulating close solder joints |

### Software Needed

- RetroPie image flashed to SD card (I reused a GamePi20 image, but a fresh image works too)
- SSH access to the Pi over WiFi

---

## Step 1: Power Subsystem (IP5306)

**Goal**: Get a stable 5V rail from the IP5306 to power everything.

### 1.1 Prepare a USB Power Input Cable

The IP5306 board needs 5V input on its VIN pad. Since my board had no USB port, I harvested a USB connector from a donor cable.

I used a USB-C connector from a cut cable. USB-C has more wires than USB-A:
- **Red wire** = VBUS (+5V)
- **Silver stranded wire** = Shield/ground (confirmed with multimeter continuity to the USB-C connector's metal shell)
- White, green = data lines (not needed, tape off)

**If you have a USB-A cable to sacrifice instead**, it's simpler: red = +5V, black = GND, white and green = data (ignore).

**Verify with multimeter**: Use continuity mode to confirm which wire is VBUS and which is GND before connecting anything.

### 1.2 Solder Connections to the IP5306 Board

I snipped and soldered short jumper wires to the IP5306's OUT-5V and GND pads for breadboard connection. The USB cable and battery were soldered directly to the board:

| IP5306 Pad | Connected To |
|------------|-------------|
| VIN | USB cable red (VBUS, +5V) |
| GND (near VIN) | USB cable ground wire |
| BAT | LiPo battery red (+) |
| GND (near BAT) | LiPo battery black (-) |
| OUT-5V | Jumper wire to breadboard + rail |
| GND (remaining) | Jumper wire to breadboard - rail |

### 1.3 Test the Power Output

1. Plug the OUT-5V and GND jumper wires into the breadboard's power rails (+ and -)
2. Plug the USB cable into a **wall charger**
3. Press the button on the IP5306 board if it doesn't auto-start
4. Set multimeter to **DC 20V** range
5. Measure across the breadboard + and - rails
6. Expected reading: **~5.0-5.2V** (I measured 5.1V)

### 1.4 IP5306 Behavior Notes

- **Auto-shutdown**: The IP5306 turns off after a few seconds if nothing is drawing current. This is normal. Once the Pi is connected and drawing power, it stays on.
- **Auto-start**: When the Pi is connected, plugging in USB power causes the IP5306 to auto-start without pressing the button. This is the desired behavior for the final build.
- **Charging**: The battery charges while the system runs (load sharing).

---

## Step 2: Boot the Pi from IP5306 Power

**Goal**: Confirm the Pi Zero runs from the IP5306's 5V output.

### 2.1 Prepare the SD Card

Before connecting the Pi, configure WiFi on the SD card for SSH access:

1. Mount the SD card's boot partition on your computer:
   ```
   sudo mkdir -p /mnt/piboot && sudo mount /dev/sdX1 /mnt/piboot
   ```
2. Create an empty file to enable SSH:
   ```
   sudo touch /mnt/piboot/ssh
   ```
3. Create WiFi config:
   ```
   sudo nano /mnt/piboot/wpa_supplicant.conf
   ```
   Contents:
   ```
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1

   network={
       ssid="Your WiFi Name"
       psk="Your WiFi Password"
   }
   ```
   SSIDs with spaces work fine inside the quotes.
4. Unmount:
   ```
   cd ~ && sudo umount /mnt/piboot
   ```

### 2.2 Connect the Pi to IP5306 Power

**Disconnect USB power first** before wiring.

| Breadboard Rail | Pi Zero Pin | Description |
|----------------|-------------|-------------|
| + rail (5V) | Pin 2 or Pin 4 | 5V power input |
| - rail (GND) | Pin 6 | Ground |

Use F-M jumper wires (Pi header pins are male, breadboard takes male -- so you need F-M).

### 2.3 Boot and Verify

1. Insert SD card into Pi
2. Plug in USB power
3. IP5306 should auto-start (LED on the board lights up)
4. Wait 60 seconds for boot
5. SSH in: `ssh pi@<IP_ADDRESS>` (default password: `raspberry`)
6. Find the Pi's IP from your router admin page or `nmap -sn 192.168.x.0/24`

---

## Step 3: Display (ILI9341 over SPI)

**Goal**: Get the ILI9341 display showing the RetroPie interface.

### 3.1 Wiring

**Power down the Pi before wiring the display.**

My ILI9341 breakout has 14 pins. The top 5 (T_IRQ, T_DO, T_DIN, T_CS, T_CLK) are for the touch panel and are left unconnected.

| Display Pin | Pi Pin | GPIO | Description |
|-------------|--------|------|-------------|
| VCC | Pin 1 | - | **3.3V (NOT 5V!)** -- 5V will damage the display |
| GND | Breadboard - rail | - | Ground |
| CS | Pin 24 | GPIO8 (CE0) | SPI chip select |
| RESET | Pin 22 | GPIO25 | Hardware reset |
| DC | Pin 18 | GPIO24 | Data/Command select |
| SDI (MOSI) | Pin 19 | GPIO10 | SPI data to display |
| SCK | Pin 23 | GPIO11 | SPI clock |
| LED | Pin 17 | - | Backlight, 3.3V (breakout has built-in current limiting) |
| SDO (MISO) | Pin 21 | GPIO9 | SPI data from display |

**Jumper wire note**: Both the Pi and the display have male header pins. You need F-F jumper wires for all display-to-Pi connections. I made mine by pulling the metal pins out of M-M dupont jumpers using fine tweezers to release the locking tab inside the housing. F-M jumpers work for display-to-breadboard (GND rail) connections.

### 3.2 Enable SPI

SSH into the Pi:
```
sudo raspi-config
```
Go to Interface Options, SPI, Enable.

### 3.3 Fix Apt Repos (Buster-based Images Only)

If using a Raspbian Buster image, the default repos are archived:
```
sudo sed -i 's|http://raspbian.raspberrypi.org/raspbian|http://legacy.raspbian.org/raspbian|g' /etc/apt/sources.list
sudo apt update
```

### 3.4 Build and Install fbcp-ili9341

```
sudo apt install -y cmake git
git clone https://github.com/juj/fbcp-ili9341.git
cd fbcp-ili9341
mkdir build && cd build
```

Build with these flags:
```
cmake -DILI9341=ON \
      -DGPIO_TFT_DATA_CONTROL=24 \
      -DGPIO_TFT_RESET_PIN=25 \
      -DSPI_BUS_CLOCK_DIVISOR=6 \
      -DSTATISTICS=0 \
      ..
```

**Important**: Verify the cmake output says `Targeting ILI9341`. If it says anything else, delete the build directory and rebuild. Stale cmake cache from a previous build can cause this.

```
make -j4
sudo cp fbcp-ili9341 /usr/local/bin/fbcp-ili9341
```

**Display rotation**: I found that no rotation flag was needed with the display pins on the left side. If your image is upside down, rebuild with `-DDISPLAY_ROTATE_180_DEGREES=ON` added to the cmake command.

### 3.5 Set fbcp-ili9341 to Run at Boot

Edit `/etc/rc.local` and add before the `exit 0` line:
```
/usr/local/bin/fbcp-ili9341 &
```

**Critical**: The first line of `/etc/rc.local` MUST be `#!/bin/sh` with no blank lines above it. A blank first line causes an "Exec format error" and the script won't run at all.

Reboot. The display should show the RetroPie splash screen instead of a white screen.

### 3.6 Display Resolution Note

The display looks slightly blurry because the HDMI framebuffer is set to 640x480 and gets scaled down to the display's native 320x240. For pixel-perfect rendering, the HDMI output should be configured to 320x240. This is a cosmetic improvement that can be done later by editing the `hdmi_cvt` line in `/boot/config.txt`.

---

## Step 4: Audio (I2S DAC + Amplifier + Speakers)

**Goal**: Get audio playing through the speakers via the PCM5102A DAC and PAM8403 amplifier.

### 4.1 PCM5102A DAC Wiring

I soldered 22 AWG solid core wire directly to the PCM5102A breakout board (it had no header pins). If your wires are stripped too high and at risk of touching, slide heat shrink tubing over them for insulation.

**Wires to breadboard rails:**

| PCM5102A Pin | Breadboard Destination | Purpose |
|-------------|----------------------|---------|
| VCC | + rail (5V) | Power |
| GND | - rail (GND) | Ground |
| FLT | - rail (GND) | Normal latency filter mode |
| DMP | - rail (GND) | De-emphasis off |
| FMT | - rail (GND) | I2S format select |
| SCL | - rail (GND) | Auto-clock mode (DAC generates its own system clock) |
| XMT | + rail (5V) | Unmute (active low, so HIGH = not muted) |

**Wires to Pi (soldered 22AWG to breakout and fed the other end into the breadboard):**

| PCM5102A Pin | Pi Pin | GPIO | Description |
|-------------|--------|------|-------------|
| 3.3V | Pin 17 | - | 3.3V power (share the pin with display's LED/VCC via breadboard bridging) |
| BCK | Pin 12 | GPIO18 | I2S bit clock |
| DIN | Pin 40 | GPIO21 | I2S serial data |
| LCK | Pin 35 | GPIO19 | I2S word clock (LRCK) |

### 4.2 PAM8403 Amplifier Wiring

I soldered the PCM5102A's L, G, and R output wires directly to the PAM8403's L, G, and R input pads. This eliminates extra breadboard connections.

**Note**: On some PAM8403 boards, the "R" (right channel input) silkscreen looks like a "B". It's R.

| PAM8403 Pin | Connected To | Notes |
|-------------|-------------|-------|
| L (input) | PCM5102A L output | Soldered directly |
| G (input) | PCM5102A G output | Soldered directly (ground) |
| R (input) | PCM5102A R output | Soldered directly |
| POWER+ | Breadboard + rail | 5V |
| POWER- | Breadboard - rail | GND |
| LOUT+ | Left speaker + | |
| LOUT- | Left speaker - | |
| ROUT+ | Right speaker + | |
| ROUT- | Right speaker - | |

### 4.3 Configure I2S Audio

SSH into the Pi and edit `/boot/config.txt`:

1. **Comment out** the built-in audio:
   ```
   #dtparam=audio=on
   ```

2. **Replace** any existing audio overlay (like `dtoverlay=audremap,pins_18_19`) with:
   ```
   dtoverlay=hifiberry-dac
   ```

   The `hifiberry-dac` overlay enables I2S output on GPIO18 (BCK), GPIO19 (LRCK), and GPIO21 (DIN).

   **Do NOT use `dtoverlay=audremap`** -- that remaps the Pi's built-in PWM audio to different pins, it does NOT enable I2S for external DACs.

3. Reboot.

### 4.4 Verify Audio

```
aplay -l
```
Should show: `snd_rpi_hifiberry_dac` as card 0.

Test with a sine wave:
```
speaker-test -t sine -f 440 -c 2 -D hw:0,0
```

You should hear a 440Hz tone from both speakers.

---

## Step 5: Buttons (GPIO Input)

**Goal**: Get physical buttons registering as input in EmulationStation.

### 5.1 Button Driver: mk_arcade_joystick_rpi

**Important**: I tried Adafruit's `retrogame` first and it does NOT work with EmulationStation on Raspbian Buster. Retrogame creates a virtual keyboard device (`/dev/input/event*` with type "retrogame"), but EmulationStation does not recognize it as a valid input device. After extensive debugging, I switched to `mk_arcade_joystick_rpi`, which creates a proper joystick device ("GPIO Controller 1") that EmulationStation natively supports.

If your RetroPie image came from a GamePi20 (or similar GPIO-based handheld), `mk_arcade_joystick_rpi` is likely already installed as a kernel module.

### 5.2 Button Wiring

Each button connects between a GPIO pin and GND. The kernel module enables internal pull-up resistors, so each GPIO pin reads HIGH normally and LOW when the button is pressed (active low).

For the prototype, I tested with two buttons (LEFT and RIGHT):

| Button | GPIO | Pi Pin | Other Leg |
|--------|------|--------|-----------|
| LEFT | GPIO4 | Pin 7 | Any GND pin or breadboard - rail |
| RIGHT | GPIO17 | Pin 11 | Any GND pin or breadboard - rail |

**Full button GPIO mapping** (configured in the driver, matching PIN_MAPPING.md):

| Position | Function | GPIO | Pi Pin |
|----------|----------|------|--------|
| 1 | UP | 12 | Pin 32 |
| 2 | DOWN | 20 | Pin 38 |
| 3 | LEFT | 4 | Pin 7 |
| 4 | RIGHT | 17 | Pin 11 |
| 5 | START | 26 | Pin 37 |
| 6 | SELECT | 16 | Pin 36 |
| 7 | A | 23 | Pin 16 |
| 8 | B | 14 | Pin 8 |
| 9 | X | 6 | Pin 31 |
| 10 | Y | 22 | Pin 15 |
| 11 | L (shoulder) | 27 | Pin 13 |
| 12 | R (shoulder) | 5 | Pin 29 |

**Breadboard note**: Tactile buttons typically have 4 legs. Two pairs of legs are internally connected. Make sure the button bridges across two different breadboard rows (one row to GPIO, one row to GND). If both legs of a connected pair are in the same row, the button is effectively a wire (always pressed). Use your multimeter in continuity mode to identify which legs are paired.

### 5.3 Configure the Kernel Module

Edit `/etc/modprobe.d/joystick.conf`:
```
options mk_arcade_joystick_rpi map=5 gpio=12,20,4,17,26,16,23,14,6,22,27,5
```

The `map=5` parameter means custom GPIO mode. The `gpio=` list assigns GPIOs in order: UP, DOWN, LEFT, RIGHT, START, SELECT, A, B, X, Y, L, R.

Make sure the module loads at boot. In `/etc/modules`:
```
mk_arcade_joystick_rpi
```

### 5.4 Configure EmulationStation Input

Edit `~/.emulationstation/es_input.cfg` (this may be symlinked to `/opt/retropie/configs/all/emulationstation/es_input.cfg`):

```xml
<?xml version="1.0"?>
<inputList>
  <inputAction type="onfinish">
    <command>/opt/retropie/supplementary/emulationstation/scripts/inputconfiguration.sh</command>
  </inputAction>
  <inputConfig type="joystick" deviceName="GPIO Controller 1" deviceGUID="15000000010000000500000000010000">
    <input name="left" type="axis" id="0" value="-1"/>
    <input name="right" type="axis" id="0" value="1"/>
    <input name="up" type="axis" id="1" value="-1"/>
    <input name="down" type="axis" id="1" value="1"/>
    <input name="a" type="button" id="0" value="1"/>
    <input name="b" type="button" id="1" value="1"/>
    <input name="x" type="button" id="4" value="1"/>
    <input name="y" type="button" id="3" value="1"/>
    <input name="start" type="button" id="11" value="1"/>
    <input name="select" type="button" id="10" value="1"/>
    <input name="pageup" type="button" id="6" value="1"/>
    <input name="pagedown" type="button" id="7" value="1"/>
  </inputConfig>
</inputList>
```

**Important**: The mk_arcade_joystick_rpi module must be loaded BEFORE EmulationStation starts. If ES starts first and finds no input devices, it logs "Added unconfigured joystick" and won't respond to input. The module is loaded at boot via `/etc/modules`, which runs before ES, so this should work automatically after a reboot.

### 5.5 Verify Buttons

After reboot, SSH in and test with evtest:
```
evtest /dev/input/event0
```

D-pad buttons should show as `EV_ABS` events (axis values -1, 0, +1). Face buttons show as `EV_KEY` events (BTN_SOUTH, BTN_EAST, etc.).

The buttons should also navigate the EmulationStation menu on the display.

---

## Complete /boot/config.txt Reference

After all prototype configuration, the relevant lines in `/boot/config.txt` are:

```ini
# SPI for display
dtparam=spi=on

# I2S audio via PCM5102A DAC (NOT audremap, NOT dtparam=audio=on)
#dtparam=audio=on
dtoverlay=hifiberry-dac

# HDMI config (for fbcp-ili9341 framebuffer copy)
hdmi_force_hotplug=1
hdmi_cvt=640 480 60 1 0 0 0
hdmi_group=2
hdmi_mode=1
hdmi_mode=87
display_rotate=2

# USB OTG
dtoverlay=dwc2,dr_mode=host

# GPU memory
gpu_mem_256=128
gpu_mem_512=256
gpu_mem_1024=256
overscan_scale=1
```

## Complete /etc/rc.local Reference

```sh
#!/bin/sh

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

# Display driver
/usr/local/bin/fbcp-ili9341 &

exit 0
```

**Critical**: First line must be `#!/bin/sh` with NO blank lines above it. A blank first line causes "Exec format error" and the entire script fails silently.

---

## Gotchas and Lessons Learned

### Power
- **IP5306 auto-shutdown**: With no load, the IP5306 turns off after a few seconds. This is normal. It stays on once the Pi draws current.
- **Use a wall charger**: PC USB ports were unreliable for charging the battery through the harvested USB-C cable. Wall chargers worked consistently.
- **Dead battery looks like a hardware failure**: If the IP5306 shuts down immediately or before the Pi finishes booting, the battery is probably dead. Plug into wall power.

### Display
- **VCC is 3.3V, NOT 5V**: The ILI9341 is a 3.3V device. Connecting VCC to 5V will damage it.
- **White screen = no driver, not broken**: A white screen with backlight on means the display is powered and wired correctly, but no software is sending pixel data over SPI.
- **fbcp-ili9341 cmake cache**: If you get the wrong display target, delete the entire build directory and rebuild. Stale cmake cache causes this.
- **rc.local formatting**: A blank line before `#!/bin/sh` causes the entire script to fail with "Exec format error". Both fbcp-ili9341 and any other startup commands will not run.

### Audio
- **Use hifiberry-dac, NOT audremap**: The `audremap` overlay remaps the Pi's built-in PWM audio, it does NOT enable I2S for external DACs. The `hifiberry-dac` overlay is what enables I2S on GPIO18/19/21.
- **Disable built-in audio**: Comment out `dtparam=audio=on` in config.txt to prevent conflicts.
- **PCM5102A config pins**: FLT, DMP, FMT, SCL all go to GND. XMT goes to HIGH (5V or 3.3V) to unmute. These are "set and forget" configuration pins.

### Buttons
- **retrogame does NOT work with EmulationStation** (on Raspbian Buster at least). It creates a virtual keyboard device that ES doesn't recognize. Use `mk_arcade_joystick_rpi` instead, which creates a proper joystick device.
- **Module load order matters**: The button driver module must be loaded before EmulationStation starts. Using `/etc/modules` handles this automatically.
- **Breadboard button orientation**: Tactile buttons have two pairs of internally-connected legs. Use continuity mode to identify the pairs. The button must bridge two different breadboard rows.
- **Loose breadboard connections**: Breadboard connections are inherently flaky. If a button works intermittently, check connections. This is a prototype limitation, not a design issue.

### General
- **Raspbian Buster repos are archived**: If using a Buster-based image, point apt at `legacy.raspbian.org` before installing packages.
- **Static**: Touch a grounded metal surface (PC chassis) before handling the Pi or breakout boards. No ESD mat needed for hobby work, just basic awareness.
- **F-F jumper shortage**: The Pi Zero 2 W has male header pins, and most breakout boards also have male pins. You will need many F-F jumpers. You can make them by pulling the metal pins out of M-M dupont jumpers using fine tweezers to release the locking tab.

---

## Subsystem Verification Checklist

| Subsystem | Status | Test Method |
|-----------|--------|-------------|
| Power (IP5306 + battery) | VERIFIED | Multimeter: 5.1V on breadboard rails |
| Compute (Pi boots from IP5306) | VERIFIED | SSH access over WiFi |
| Display (ILI9341 over SPI) | VERIFIED | RetroPie splash screen visible on display |
| Audio (I2S -> DAC -> amp -> speakers) | VERIFIED | `speaker-test -t sine -f 440 -c 2 -D hw:0,0` produces sound from both speakers |
| Buttons (GPIO via mk_arcade_joystick_rpi) | VERIFIED | `evtest` shows button events; buttons navigate EmulationStation menu |
| Play-while-charging (IP5306 load sharing) | VERIFIED | System runs on wall power while battery charges |
