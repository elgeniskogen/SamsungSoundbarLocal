DOMAIN = "ipsamsung_soundbar"
DEFAULT_NAME = "Samsung Soundbar"
DEFAULT_PORT = 56001

CONF_NAME = "name"

SOURCE_MAP = {
    "hdmi1": "hdmi1",
    "hdmi2": "hdmi2",
    "optical": "optical",
    "bt": "bt",
}

SOURCE_LIST = list(SOURCE_MAP.keys())

# Not selectable via SetFunc on the HW-Q960A (confirmed: SetFunc wifi/wifiidle
# do not switch sources). Used only to label the source when GetFunc repeatedly
# fails to return a <function> value while the unit is confirmed powered on -
# the observed symptom of the soundbar being on a network-audio source.
SOURCE_WIFI = "wifi"

# Consecutive failed GetFunc reads (while powered on) required before inferring
# SOURCE_WIFI, to avoid flagging a single transient network hiccup as Wi-Fi.
WIFI_INFERENCE_THRESHOLD = 2

# Sound Mode is readable directly via GetSoundMode (confirmed working on the
# HW-Q960A), but there is no working local UIC write command for it - the
# guessed "SetSoundMode" (and several parameter/value variants) was tested
# and does not work. Setting it therefore goes through a Harmony-controlled
# remote instead; see select.py.
SOUND_MODE_LIST = ["standard", "surround", "game", "adaptive sound"]

# Existing Harmony hub/device/command used to reach the soundbar's physical
# Sound Mode button. The button cycles through modes rather than selecting
# one directly, so select.py must drive it in a closed loop against
# GetSoundMode rather than assume a press succeeded or which mode it lands on.
HARMONY_REMOTE_ENTITY_ID = "remote.kjellerstue"
HARMONY_DEVICE = "Samsung Amp"
HARMONY_SOUND_MODE_COMMAND = "SoundMode"

# With 4 known modes arranged in a confirmed cycle (standard -> surround ->
# game -> adaptive sound -> standard), at most 3 presses are ever needed to
# reach any target from any starting mode once the receiver is responsive.
# From a cold/idle state, live testing showed the first 2 presses after a
# period of inactivity are consumed waking the receiver and showing current
# status, with no mode change, before cycling begins on the 3rd press and
# continues 1:1 on every press after that. Budget for the worst case: 2
# wasted cold-start presses + 3 real cycle steps = 5.
SOUND_MODE_MAX_PRESSES = 5

# How often to re-check GetSoundMode after a press, and how long to wait for
# a change before giving up on that press and trying the next one.
SOUND_MODE_POLL_INTERVAL = 0.25
SOUND_MODE_STEP_TIMEOUT = 1.0
