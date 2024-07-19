"""Constants for the sensecraft integration."""

DOMAIN = "sensecraft"

ENV_CHINA = "china"
ENV_GLOBAL = "global"
SUPPORTED_ENV = [ENV_CHINA, ENV_GLOBAL]
JETSON_NAME = "Jetson"
GROVE_AI_V2_NAME = "grove_vision_ai_v2"
SUPPORTED_DEVICE = [JETSON_NAME, GROVE_AI_V2_NAME]

SELECTED_DEVICE = "selected_device"
ACCOUNT_USERNAME = "username"
ACCOUNT_PASSWORD = "password"

DATA_SOURCE = "data_source"
SENSECRAFT = "sensecraft"
SSCMA = "sscma"
CLOUD = "cloud"

ACCOUNT_ENV = "env"

DEVICE_NAME = "device_name"
DEVICE_HOST = "device_host"
DEVICE_PORT = "device_port"
DEVICE_MAC = "device_mac"
DEVICE_ID = "device_id"
DEVICE_TYPE = "device_type"
SENSECRAFT_CLOUD = "sensecraft_cloud"
SENSECRAFT_LOCAL = "sensecraft_local"
SSCMA_LOCAL = "sscma_local"
CONFIG_DATA = "config_data"
MQTT_BROKER = "mqtt_broker"
MQTT_PORT = "mqtt_port"

BROKER = "broker"
PORT = "port"
MQTT_TOPIC = "mqtt_topic"

MEASUREMENT_DICT = {
    "4097": [
        "Air Temperature",
        "℃",
        "mdi:snowflake-thermometer"
    ],
    "4098": [
        "Air Humidity",
        "% RH",
        "mdi:water-percent"
    ],
    "4099": [
        "Light Intensity",
        "Lux",
        "mdi:wall-sconce-round"
    ],
    "4100": [
        "CO2",
        "ppm",
        "mdi:molecule-co2"
    ],
    "4101": [
        "Barometric Pressure",
        "Pa",
        "mdi:car-brake-low-pressure"
    ],
    "4102": [
        "Soil Temperature",
        "℃",
        "mdi:oil-temperature"
    ],
    "4103": [
        "Soil Moisture",
        "%",
        "mdi:water-percent"
    ],
    "4104": [
        "Wind Direction",
        "°",
        "mdi:sign-direction"
    ],
    "4105": [
        "Wind Speed",
        "m/s",
        "mdi:weather-windy"
    ],
    "4106": [
        "pH",
        "PH",
        "mdi:ph"
    ],
    "4107": [
        "Light Quantum",
        "umol/㎡s",
        "mdi:wall-sconce-round"
    ],
    "4108": [
        "Electrical Conductivity",
        "mS/cm",
        "mdi:devices"
    ],
    "4109": [
        "Dissolved Oxygen",
        "mg/L",
        "mdi:devices"
    ],
    "4110": [
        "Soil Volumetric Water Content",
        "%",
        "mdi:devices"
    ],
    "4111": [
        "Soil Electrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4112": [
        "Soil Temperature(Soil Temperature, VWC & EC Sensor)",
        "℃",
        "mdi:oil-temperature"
    ],
    "4113": [
        "Rainfall Hourly",
        "mm/hour",
        "mdi:weather-rainy"
    ],
    "4115": [
        "Distance",
        "cm",
        "mdi:walk"
    ],
    "4116": [
        "Water Leak",
        "",
        "mdi:leak"
    ],
    "4117": [
        "Liguid Level",
        "cm",
        "mdi:liquid-spot"
    ],
    "4118": [
        "NH3",
        "ppm",
        "mdi:bottle-tonic-skull"
    ],
    "4119": [
        "H2S",
        "ppm",
        "mdi:bottle-tonic-skull"
    ],
    "4120": [
        "Flow Rate",
        "m3/h",
        "mdi:devices"
    ],
    "4121": [
        "Total Flow",
        "m3",
        "mdi:devices"
    ],
    "4122": [
        "Oxygen Concentration",
        "%vol",
        "mdi:gas-cylinder"
    ],
    "4123": [
        "Water Eletrical Conductivity",
        "us/cm",
        "mdi:flash"
    ],
    "4124": [
        "Water Temperature",
        "℃",
        "mdi:oil-temperature"
    ],
    "4125": [
        "Soil Heat Flux",
        "W/㎡",
        "mdi:printer-3d-nozzle-heat"
    ],
    "4126": [
        "Sunshine Duration",
        "h",
        "mdi:clock-time-four-outline"
    ],
    "4127": [
        "Total Solar Radiation",
        "W/㎡",
        "mdi:radioactive"
    ],
    "4128": [
        "Water Surface Evaporation",
        "mm",
        "mdi:waves-arrow-up"
    ],
    "4129": [
        "Photosynthetically Active Radiation(PAR)",
        "umol/㎡s",
        "mdi:waves-arrow-up"
    ],
    "4130": [
        "Accelerometer",
        "m/s",
        "mdi:rotate-orbit"
    ],
    "4131": [
        "Sound Intensity",
        "",
        "mdi:home-sound-in"
    ],
    "4133": [
        "Soil Tension",
        "KPA",
        "mdi:devices"
    ],
    "4134": [
        "Salinity",
        "mg/L",
        "mdi:devices"
    ],
    "4135": [
        "TDS",
        "mg/L",
        "mdi:devices"
    ],
    "4136": [
        "Leaf Temperature",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4137": [
        "Leaf Wetness",
        "%",
        "mdi:water-percent"
    ],
    "4138": [
        "Soil Moisture-10cm",
        "%",
        "mdi:water-percent"
    ],
    "4139": [
        "Soil Moisture-20cm",
        "%",
        "mdi:water-percent"
    ],
    "4140": [
        "Soil Moisture-30cm",
        "%",
        "mdi:water-percent"
    ],
    "4141": [
        "Soil Moisture-40cm",
        "%",
        "mdi:water-percent"
    ],
    "4142": [
        "Soil Temperature-10cm",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4143": [
        "Soil Temperature-20cm",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4144": [
        "Soil Temperature-30cm",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4145": [
        "Soil Temperature-40cm",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4146": [
        "PM2.5",
        "μg/m3",
        "mdi:devices"
    ],
    "4147": [
        "PM10",
        "μg/m3",
        "mdi:devices"
    ],
    "4148": [
        "Noise",
        "dB",
        "mdi:home-sound-in"
    ],
    "4150": [
        "AccelerometerX",
        "m/s²",
        "mdi:axis-arrow"
    ],
    "4151": [
        "AccelerometerY",
        "m/s²",
        "mdi:axis-arrow"
    ],
    "4152": [
        "AccelerometerZ",
        "m/s²",
        "mdi:axis-arrow"
    ],
    "4154": [
        "Salinity",
        "PSU",
        "mdi:devices"
    ],
    "4155": [
        "ORP",
        "mV",
        "mdi:devices"
    ],
    "4156": [
        "Turbidity",
        "NTU",
        "mdi:devices"
    ],
    "4157": [
        "Ammonia ion",
        "mg/L",
        "mdi:devices"
    ],
    "4158": [
        "Eletrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4159": [
        "Eletrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4160": [
        "Eletrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4161": [
        "Eletrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4162": [
        "N Content",
        "mg/kg",
        "mdi:devices"
    ],
    "4163": [
        "P Content",
        "mg/kg",
        "mdi:devices"
    ],
    "4164": [
        "K Content",
        "mg/kg",
        "mdi:devices"
    ],
    "4165": [
        "Measurement1",
        " ",
        "mdi:devices"
    ],
    "4166": [
        "Measurement2",
        " ",
        "mdi:devices"
    ],
    "4167": [
        "Measurement3",
        " ",
        "mdi:devices"
    ],
    "4168": [
        "Measurement4",
        " ",
        "mdi:devices"
    ],
    "4169": [
        "Measurement5",
        " ",
        "mdi:devices"
    ],
    "4170": [
        "Measurement6",
        " ",
        "mdi:devices"
    ],
    "4171": [
        "Measurement7",
        " ",
        "mdi:devices"
    ],
    "4172": [
        "Measurement8",
        " ",
        "mdi:devices"
    ],
    "4173": [
        "Measurement9",
        " ",
        "mdi:devices"
    ],
    "4174": [
        "Measurement10",
        " ",
        "mdi:devices"
    ],
    "4175": [
        "AI Detection No.01",
        " ",
        "mdi:devices"
    ],
    "4176": [
        "AI Detection No.02",
        " ",
        "mdi:devices"
    ],
    "4177": [
        "AI Detection No.03",
        " ",
        "mdi:devices"
    ],
    "4178": [
        "AI Detection No.04",
        " ",
        "mdi:devices"
    ],
    "4179": [
        "AI Detection No.05",
        " ",
        "mdi:devices"
    ],
    "4180": [
        "AI Detection No.06",
        " ",
        "mdi:devices"
    ],
    "4181": [
        "AI Detection No.07",
        " ",
        "mdi:devices"
    ],
    "4182": [
        "AI Detection No.08",
        " ",
        "mdi:devices"
    ],
    "4183": [
        "AI Detection No.09",
        " ",
        "mdi:devices"
    ],
    "4184": [
        "AI Detection No.10",
        " ",
        "mdi:devices"
    ],
    "4190": [
        "UV Index",
        " ",
        "mdi:devices"
    ],
    "4191": [
        "Peak Wind Gust",
        "m/s",
        "mdi:weather-windy"
    ],
    "4192": [
        "Sound Intensity",
        "dB",
        "mdi:home-sound-in"
    ],
    "4193": [
        "Light Intensity",
        " ",
        "mdi:desk-lamp"
    ],
    "4195": [
        "TVOC",
        " ppb",
        "mdi:devices"
    ],
    "4196": [
        "Soil moisture intensity",
        " ",
        "mdi:water-percent-alert"
    ],
    "4197": [
        "longitude",
        "°",
        "mdi:longitude"
    ],
    "4198": [
        "latitude",
        "°",
        "mdi:latitude"
    ],
    "4199": [
        "Light",
        "%",
        "mdi:desk-lamp"
    ],
    "4200": [
        "SOS Event",
        " ",
        "mdi:car-brake-alert"
    ],
    "4201": [
        "Ultraviolet Radiation",
        "W/㎡",
        "mdi:radioactive"
    ],
    "4202": [
        "Dew point temperature",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4203": [
        "Temperature",
        "℃",
        "mdi:temperature-celsius"
    ],
    "4204": [
        "Soil Pore Water Eletrical Conductivity",
        "mS/cm",
        "mdi:flash"
    ],
    "4205": [
        "Epsilon",
        " ",
        "mdi:epsilon"
    ],
    "4206": [
        "VOC_INDEX",
        " ",
        "mdi:devices"
    ],
    "4207": [
        "Noise",
        " ",
        "mdi:home-sound-in"
    ],
    "4208": [
        "Custom event",
        " ",
        "mdi:car-brake-alert"
    ],
    "5001": [
        "Wi-Fi MAC Address",
        " ",
        "mdi:wifi"
    ],
    "5002": [
        "Bluetooth Beacon MAC Address",
        " ",
        "mdi:bluetooth"
    ],
    "5003": [
        "Event Status",
        " ",
        "mdi:alert-box-outline"
    ],
    "5100": [
        "Switch",
        "",
        "mdi:toggle-switch"
    ],
    "3000": [
        "Battery",
        "",
        "mdi:battery"
    ],
}
