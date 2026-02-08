"""Constants for the Heating Curve Calculator integration."""

DOMAIN = "heating_curve"

# Configuration keys
CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_ROOM_SENSOR = "room_sensor"
CONF_CURVE_SLOPE = "curve_slope"
CONF_CURVE_LEVEL = "curve_level"
CONF_ROOM_TEMP_TARGET = "room_temp_target"
CONF_MIN_FLOW_TEMP = "min_flow_temp"
CONF_MAX_FLOW_TEMP = "max_flow_temp"
CONF_CALCULATION_MODE = "calculation_mode"
CONF_HYSTERESIS = "hysteresis"

# Calculation modes
MODE_CLASSIC = "classic"
MODE_WITH_ROOM_TEMP = "with_room_temp"

CALCULATION_MODES = [MODE_CLASSIC, MODE_WITH_ROOM_TEMP]

# Default values
DEFAULT_CURVE_SLOPE = 1.4
DEFAULT_CURVE_LEVEL = 0.0
DEFAULT_ROOM_TEMP_TARGET = 20.0
DEFAULT_MIN_FLOW_TEMP = 20.0
DEFAULT_MAX_FLOW_TEMP = 75.0
DEFAULT_CALCULATION_MODE = MODE_CLASSIC
DEFAULT_HYSTERESIS = 1.0


