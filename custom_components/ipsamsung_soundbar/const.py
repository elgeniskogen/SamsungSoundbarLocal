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
