# Samsung Soundbar Local IP (Home Assistant HACS Integration)

Local-only Home Assistant integration for Samsung soundbars using the WAM/UIC HTTP API.

## Status

This repository is now structured as a proper HACS custom integration:

- `custom_components/ipsamsung_soundbar/`
- Config flow enabled
- Media player platform registered correctly

## HACS Installation

1. In HACS, add this repository as a **Custom repository**.
2. Category: **Integration**.
3. Install **Samsung Soundbar Local IP**.
4. Restart Home Assistant.
5. Go to **Settings -> Devices & Services -> Add Integration**.
6. Search for **Samsung Soundbar Local IP**.
7. Enter:
   - Host/IP (example: `192.168.1.5`)
   - Port (default: `56001`)
   - Name

## What This Integration Supports

- Power: `turn_on`, `turn_off` via `SetPowerStatus` (verified reliable on HW-Q960A; raw `PowerOn`/`PowerOff` are not used - confirmed non-functional on that model)
- Volume:
  - Set absolute volume (`0-100`)
  - Volume up/down (implemented as absolute +/-1)
- Mute: on/off
- Source select:
  - `hdmi1`, `hdmi2`, `optical`, `bt`
  - `optical` covers both the TOSLINK "Digital Audio In" port and TV audio received via HDMI-ARC - these are the same underlying mode on the HW-Q960A, not separate sources
  - Wi-Fi/AirPlay/Spotify Connect cannot be selected locally (no working `SetFunc` value) and is only inferred for display when `GetFunc` repeatedly fails to respond while the unit is powered on
- Polling state:
  - power status
  - volume
  - mute
  - source (see Wi-Fi caveat above)

## Command Behavior Notes (N950 Testing)

Reliable:
- `<name>GetVolume</name>`
- `<name>SetVolume</name><p type="dec" name="volume" val="N"/>`
- `<name>GetMute</name>`
- `<name>SetMute</name><p type="str" name="mute" val="on|off"/>`
- `<name>GetFunc</name>`
- `<name>SetFunc</name><p type="str" name="function" val="hdmi1|hdmi2|optical|arc|bt"/>`

Less reliable (firmware dependent):
- `<name>PowerOn</name>`
- `<name>PowerOff</name>`

The integration attempts power fallback logic when possible.

## Command Behavior Notes (HW-Q960A Testing)

Directly verified against a Samsung HW-Q960A (protocolver 2.3, platform tizen30):

Reliable:
- `<name>GetPowerStatus</name>` - responds correctly even while the unit is off (no need to assume state when unreachable)
- `<name>SetPowerStatus</name><p type="dec" name="power" val="1"/>` - turns on
- `<name>SetPowerStatus</name><p type="dec" name="power" val="0"/>` - turns off
- `<name>SetFunc</name><p type="str" name="function" val="hdmi1|hdmi2|optical|bt"/>` - all confirmed via follow-up `GetFunc`

Confirmed NOT working on this model:
- `<name>PowerOn</name>` / `<name>PowerOff</name>` - no effect; the device can still reply with `result="ok"` on an unrelated stray status message, so this attribute alone cannot be trusted as confirmation of the requested action
- `<name>SetFunc</name><p type="str" name="function" val="arc"/>` - no effect. `GetFeature` reports `<arc>0</arc>` and has no `arc` entry in `inputmode`; TV audio via HDMI-ARC uses the same `optical` mode as the physical TOSLINK "Digital Audio In" port, not a separate identifier
- `<name>SetFunc</name><p type="str" name="function" val="wifi"/>` and `val="wifiidle"` - do not switch the source

Known limitation - Wi-Fi/network audio (AirPlay, Spotify Connect):
- The soundbar can switch itself into this mode on its own (e.g. starting AirPlay while on HDMI1), with no command from Home Assistant
- While active, `GetFunc`, `GetPlayStatus`, `GetMusicInfo`, `GetCurrentPlayTime` and `GetCurrentPlaylist` stop returning their real data and instead echo an unrelated queued status message (still `result="ok"`)
- There is no confirmed way to read or select this source directly; the integration infers it only after repeated consecutive `GetFunc` failures while the unit is confirmed powered on

## Detailed Command Reference

All commands below use Samsung WAM/UIC HTTP control.

- **Base URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=<URL_ENCODED_XML>`
- Replace `<IP_ADDRESS>` with your soundbar IP.
- `status=working` means confirmed in local testing.

### Confirmed Working Commands

#### Get 7-Band EQ List
- **Status:** `working`
- **Purpose:** Returns EQ presets/modes
- **XML:** `<name>Get7BandEQList</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGet7BandEQList%3C%2Fname%3E`

#### Get AP Info
- **Status:** `working`
- **Purpose:** Returns network/ap details
- **XML:** `<name>GetApInfo</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetApInfo%3C%2Fname%3E`

#### Get Current EQ Mode
- **Status:** `working`
- **Purpose:** Returns active EQ mode
- **XML:** `<name>GetCurrentEQMode</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetCurrentEQMode%3C%2Fname%3E`

#### Get Feature Matrix
- **Status:** `working`
- **Purpose:** Returns supported inputs/features for this firmware
- **XML:** `<name>GetFeature</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetFeature%3C%2Fname%3E`

#### Get Input Function
- **Status:** `working`
- **Purpose:** Returns active input
- **XML:** `<name>GetFunc</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetFunc%3C%2Fname%3E`

#### Get Main Info
- **Status:** `working`
- **Purpose:** Returns overall device state
- **XML:** `<name>GetMainInfo</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetMainInfo%3C%2Fname%3E`

#### Get Mute
- **Status:** `working`
- **Purpose:** Returns on/off
- **XML:** `<name>GetMute</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetMute%3C%2Fname%3E`

#### Get Power Status
- **Status:** `working`
- **Purpose:** Returns powerStatus (0/1)
- **XML:** `<name>GetPowerStatus</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetPowerStatus%3C%2Fname%3E`

#### Get Sound Mode
- **Status:** `working`
- **Purpose:** Returns current sound mode
- **XML:** `<name>GetSoundMode</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetSoundMode%3C%2Fname%3E`

#### Get Volume
- **Status:** `working`
- **Purpose:** Returns current volume 0-100
- **XML:** `<name>GetVolume</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetVolume%3C%2Fname%3E`

#### Get Woofer Level
- **Status:** `working`
- **Purpose:** Returns woofer level
- **XML:** `<name>GetWooferLevel</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetWooferLevel%3C%2Fname%3E`

#### Set 7-Band EQ Mode
- **Status:** `working`
- **Purpose:** Sets EQ preset index
- **XML:** `<name>Set7bandEQMode</name><p type="dec" name="presetindex" val="1"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESet7bandEQMode%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22presetindex%22%20val%3D%221%22%2F%3E`

#### Set 7-Band EQ Values (Flat Example)
- **Status:** `working`
- **Purpose:** Writes 7-band values
- **XML:** `<name>Set7bandEQValue</name><p type="dec" name="presetindex" val="4"/><p type="dec" name="eqvalue1" val="0"/><p type="dec" name="eqvalue2" val="0"/><p type="dec" name="eqvalue3" val="0"/><p type="dec" name="eqvalue4" val="0"/><p type="dec" name="eqvalue5" val="0"/><p type="dec" name="eqvalue6" val="0"/><p type="dec" name="eqvalue7" val="0"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESet7bandEQValue%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22presetindex%22%20val%3D%224%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue1%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue2%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue3%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue4%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue5%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue6%22%20val%3D%220%22%2F%3E%3Cp%20type%3D%22dec%22%20name%3D%22eqvalue7%22%20val%3D%220%22%2F%3E`

#### Set Input ARC
- **Status:** `working` on N950; **confirmed NOT working on HW-Q960A** (see Q960A notes above - `GetFeature` reports `<arc>0</arc>`, no effect when sent)
- **Purpose:** Switches to ARC
- **XML:** `<name>SetFunc</name><p type="str" name="function" val="arc"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetFunc%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22function%22%20val%3D%22arc%22%2F%3E`

#### Set Input Bluetooth
- **Status:** `working`
- **Purpose:** Switches to Bluetooth
- **XML:** `<name>SetFunc</name><p type="str" name="function" val="bt"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetFunc%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22function%22%20val%3D%22bt%22%2F%3E`

#### Set Input HDMI1
- **Status:** `working`
- **Purpose:** Switches to HDMI1
- **XML:** `<name>SetFunc</name><p type="str" name="function" val="hdmi1"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetFunc%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22function%22%20val%3D%22hdmi1%22%2F%3E`

#### Set Input HDMI2
- **Status:** `working`
- **Purpose:** Switches to HDMI2
- **XML:** `<name>SetFunc</name><p type="str" name="function" val="hdmi2"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetFunc%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22function%22%20val%3D%22hdmi2%22%2F%3E`

#### Set Input Optical
- **Status:** `working`
- **Purpose:** Switches to optical
- **XML:** `<name>SetFunc</name><p type="str" name="function" val="optical"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetFunc%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22function%22%20val%3D%22optical%22%2F%3E`

#### Set Mute Off
- **Status:** `working`
- **Purpose:** Unmutes the soundbar
- **XML:** `<name>SetMute</name><p type="str" name="mute" val="off"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetMute%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22mute%22%20val%3D%22off%22%2F%3E`

#### Set Mute On
- **Status:** `working`
- **Purpose:** Mutes the soundbar
- **XML:** `<name>SetMute</name><p type="str" name="mute" val="on"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetMute%3C%2Fname%3E%3Cp%20type%3D%22str%22%20name%3D%22mute%22%20val%3D%22on%22%2F%3E`

#### Set Volume (Absolute)
- **Status:** `working`
- **Purpose:** Sets volume to explicit value
- **XML:** `<name>SetVolume</name><p type="dec" name="volume" val="10"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetVolume%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22volume%22%20val%3D%2210%22%2F%3E`

#### Set Volume via delta (acts absolute)
- **Status:** `working`
- **Purpose:** Acts as absolute set on this device
- **XML:** `<name>SetVolume</name><p type="dec" name="delta" val="10"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetVolume%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22delta%22%20val%3D%2210%22%2F%3E`

#### Set Woofer +6
- **Status:** `working`
- **Purpose:** Sets woofer to +6
- **XML:** `<name>SetWooferLevel</name><p type="dec" name="wooferlevel" val="6"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetWooferLevel%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22wooferlevel%22%20val%3D%226%22%2F%3E`

#### Set Woofer -6
- **Status:** `working`
- **Purpose:** Sets woofer to -6
- **XML:** `<name>SetWooferLevel</name><p type="dec" name="wooferlevel" val="-6"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetWooferLevel%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22wooferlevel%22%20val%3D%22-6%22%2F%3E`

### Known Unreliable / Not Working Commands

#### Power Off (Raw)
- **Status:** `not_working`
- **Purpose:** Timed out during repeated tests
- **XML:** `<name>PowerOff</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EPowerOff%3C%2Fname%3E`

#### Power On (Raw)
- **Status:** `not_working`
- **Purpose:** Timed out during repeated tests
- **XML:** `<name>PowerOn</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EPowerOn%3C%2Fname%3E`

#### Set Power Status Off (Flaky)
- **Status:** `not_working`
- **Purpose:** May set powerStatus=0; not fully reliable
- **XML:** `<name>SetPowerStatus</name><p type="dec" name="power" val="0"/>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetPowerStatus%3C%2Fname%3E%3Cp%20type%3D%22dec%22%20name%3D%22power%22%20val%3D%220%22%2F%3E`

#### Volume Down (Raw)
- **Status:** `not_working`
- **Purpose:** Mostly timeout/no state change
- **XML:** `<name>VolumeDown</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EVolumeDown%3C%2Fname%3E`

#### Volume Up (Raw)
- **Status:** `not_working`
- **Purpose:** Mostly timeout/no state change
- **XML:** `<name>VolumeUp</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EVolumeUp%3C%2Fname%3E`

### Additional Known Commands (Observed In WAM Docs, Not Confirmed Here)

#### GetEQBalance
- **Status:** `unconfirmed`
- **Purpose:** Query EQ balance (timed out in local testing)
- **XML:** `<name>GetEQBalance</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetEQBalance%3C%2Fname%3E`

#### SetEQBalance
- **Status:** `unconfirmed`
- **Purpose:** Set EQ balance with `dec balance`
- **XML:** `<name>SetEQBalance</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetEQBalance%3C%2Fname%3E`

#### GetBass
- **Status:** `unconfirmed`
- **Purpose:** Query bass level
- **XML:** `<name>GetBass</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetBass%3C%2Fname%3E`

#### SetBass
- **Status:** `unconfirmed`
- **Purpose:** Set bass level
- **XML:** `<name>SetBass</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetBass%3C%2Fname%3E`

#### GetTreble
- **Status:** `unconfirmed`
- **Purpose:** Query treble level
- **XML:** `<name>GetTreble</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3EGetTreble%3C%2Fname%3E`

#### SetTreble
- **Status:** `unconfirmed`
- **Purpose:** Set treble level
- **XML:** `<name>SetTreble</name>`
- **Test URL:** `http://<IP_ADDRESS>:56001/UIC?cmd=%3Cname%3ESetTreble%3C%2Fname%3E`

## Advanced Reference

For contributors extending command coverage across Samsung models, see:

- [`docs/COMMAND_REFERENCE.md`](docs/COMMAND_REFERENCE.md)

It includes payload patterns, reliability notes, command families, and a safe discovery workflow.

## Local Harness (Optional)

A local command harness is also included for research/testing:

```bash
python3 app.py
```

Then open `http://127.0.0.1:8787`.

## Troubleshooting

If the integration still does not load in Home Assistant:

1. Confirm files exist under:
   - `custom_components/ipsamsung_soundbar/manifest.json`
   - `custom_components/ipsamsung_soundbar/__init__.py`
   - `custom_components/ipsamsung_soundbar/media_player.py`
2. Restart Home Assistant after install/update.
3. Check **Settings -> System -> Logs** for `ipsamsung_soundbar` errors.
4. Confirm the soundbar responds on `56001`:

```bash
curl 'http://<IP>:56001/UIC?cmd=%3Cname%3EGetFeature%3C/name%3E'
```

## Disclaimer

This is an unofficial reverse-engineered integration. Command support varies by soundbar model and firmware.
