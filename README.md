# Falchion Light

Local Python 3 userspace lighting controller for the wired ASUS ROG
Falchion RX Low Profile, USB 0b05:1b04, firmware reported as 04.00.04.00.
Uses the existing Linux hidraw driver. No daemon, downloaded executable,
third-party Python dependency, or custom kernel module.

## Installed usage

Run `man falchion-light` for the full command reference and usage examples.

```sh
falchion-light info
falchion-light probe
falchion-light set static 336699 --brightness 50
falchion-light set static ff8800 --brightness 25
falchion-light set static 336699 --brightness 0
```

Hex colors may have a leading # if quoted. Brightness is 0..100.
`set` always specifies a complete effect, color and brightness; it does not
attempt to infer the previous hardware state. Default brightness is 50%.
The last example turns lighting off; repeat a nonzero command to restore it.

### Lighting effect examples

```sh
# Blue breathing
falchion-light set breathing 336699 --speed slow --brightness 50

# Rainbow color cycle
falchion-light set cycle 000000 --speed medium --brightness 50

# Rainbow wave moving across the keys
falchion-light set wave 000000 --speed slow --brightness 50

# Blue glow on keypress
falchion-light set reactive 336699 --brightness 50

# Starry night
falchion-light set starry 336699 --speed slow --brightness 50

# Raindrops
falchion-light set raindrop 336699 --speed medium --brightness 50

# Return to steady blue
falchion-light set static 336699 --brightness 50
```

`--speed` accepts `slow`, `medium`, or `fast`; the default is `medium`.
For `cycle` and `wave`, `000000` is a required placeholder color that the effect ignores.
Static lighting and rainbow wave have been visually confirmed on this unit.
The other animated modes follow community protocol evidence and remain
unverified here.

The wave command was tested with the three-packet sequence described in
G-Helper's Falchion RX implementation. All three packets returned the expected
responses; the rainbow wave was visually confirmed on the test keyboard. It runs in the keyboard hardware
without continuous software updates.

### Additional options

`--dry-run` prints the HID report without opening the device.
`--save` explicitly sends the documented apply/save command after setting
the effect. The keyboard acknowledged saving the rainbow wave at slow speed
and 50% brightness. Without this option, the tool sends no explicit save
command. Persistence across power cycles still needs confirmation.

### Save the wave as the keyboard default

```sh
falchion-light set wave 000000 --speed slow --brightness 50 --save
```

This sends the onboard apply/save command, which the keyboard acknowledged.
Check persistence by switching the keyboard off and on, then reconnecting it.
If the wave returns without running the command, no Linux startup task is needed.

## Validation and limits

On 2026-10-15, the version query and static 336699 at 50% brightness returned
the expected responses. Steady blue lighting was visually confirmed on the test keyboard.
Wired USB only; receiver and Bluetooth operation are unsupported.

Discovery requires exactly one matching USB model, interface 01, and an exact
vendor-control HID descriptor. Both identity and descriptor are rechecked
using ioctl after opening. The program locks the interface, uses nonblocking
I/O, bounded response draining and one-second poll timeouts, and checks echoed
command bytes. No automatic write retries, raw-command facility, firmware
updates, keyboard resets, or input-interface reads are implemented.

From the project directory, run hardware-free tests with:

```sh
python3 -m unittest discover -v
```

## Permissions and installation

Requires Linux, Python 3, and udev/logind for active-session device access.
Only the wired ASUS ROG Falchion RX Low Profile USB `0b05:1b04` has been tested;
other Falchion variants are unsupported.

Clone the repository and install the executable and manual page:

```sh
git clone https://github.com/ChipGillespie/falchion-light.git
cd falchion-light
install -Dm0755 falchion-light ~/.local/bin/falchion-light
install -Dm0644 falchion-light.1 ~/.local/share/man/man1/falchion-light.1
```

Ensure `~/.local/bin` is in your `PATH`. Review the rule and helper before
installing device permissions with:

```sh
sudo bash ./install-device-access.sh
```

The helper refuses to overwrite an existing rule. Reconnect the keyboard
while logged into your local desktop session if access is not immediately
available. Run `falchion-light info` first to check discovery without sending
commands, then `falchion-light probe` to query the firmware version.

The rule grants the active local desktop user read/write access only to
the vendor interface of this exact wired model through udev/logind uaccess.
It does not grant access to the keyboard's typing interfaces. Programs
running as the active user can issue vendor commands through the granted
interface, so this is still a device-access permission grant.

No system service or startup job is required. Source changes require reinstalling
the executable with `install -m 0755 falchion-light ~/.local/bin/falchion-light`.

## Removal

Remove the installed user executable and the single rule, reload udev, then
unplug/replug the keyboard to revoke the current device ACL:

```sh
rm ~/.local/bin/falchion-light
rm ~/.local/share/man/man1/falchion-light.1
sudo rm /etc/udev/rules.d/70-falchion-light.rules
sudo udevadm control --reload-rules
```

The source directory can remain for inspection. Lighting can also be adjusted
with the keyboard's Fn+arrow shortcuts.

## Protocol evidence

Community reference source reviewed at commit c8ae06a:
https://github.com/rahulrajaram/rogdriver

Vendor payloads: version query 12 00; effect 51 2c followed by mode, reserved
zero, speed, brightness, color mode, direction, per-LED flag 02, and RGB;
optional apply/save 50 55. The original source's write framing was not reused.

Kernel HID API documentation requires a zero report-number byte before an
unnumbered output report (65 bytes including 64 payload bytes):
https://docs.kernel.org/hid/hidraw.html

Wave protocol evidence: G-Helper commit dd2dced63fbd6e5abb1a50d88b738f7159f5e71d,
`app/Peripherals/Keyboard/Models/Falchion.cs` and `AsusKeyboard.cs`:
https://github.com/seerge/g-helper/tree/dd2dced63fbd6e5abb1a50d88b738f7159f5e71d/app/Peripherals/Keyboard

For USB 1b04, mode 04 requires three 51 2c packets with countdown tags 02, 01,
00. Only the first carries speed, brightness, random-color flag 01, direction
00 and per-LED flag 02. This replaces the unsupported single-packet approach.
