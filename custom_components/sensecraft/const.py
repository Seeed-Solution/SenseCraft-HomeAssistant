"""Constants for the sensecraft integration."""

DOMAIN = "sensecraft"

ENV_CHINA = "china"
ENV_GLOBAL = "global"
SUPPORTED_ENV = [ENV_CHINA, ENV_GLOBAL]
SELECTED_DEVICE = "selected_device"
ACCOUNT_USERNAME = "username"
ACCOUNT_PASSWORD = "password"

ACCESS_ID = "access_id"
ACCESS_KEY = "access_key"
ACCOUNT_ENV = "env"
ACCOUNT_PASSWORD = "password"
ORG_ID = "orgID"


PORTAL = "portal"
OPENAPI = "openapi"
OPENSTREAM = "openstream"

ENV_URL = {
    ENV_CHINA: {
        PORTAL: 'https://sensecap.seeed.cn/portalapi',
        OPENAPI: 'https://sensecap.seeed.cn/openapi',
        OPENSTREAM: 'sensecap-openstream.seeed.cn',
    },
    ENV_GLOBAL: {
        PORTAL: 'https://sensecap.seeed.cc/portalapi',
        OPENAPI: 'https://sensecap.seeed.cc/openapi',
        OPENSTREAM: 'sensecap-openstream.seeed.cc',   
    }
}

MEASUREMENT_DICT = {
    "4097": [
        "Air Temperature",
        "℃"
    ],
    "4098": [
        "Air Humidity",
        "% RH"
    ],
    "4099": [
        "Light Intensity",
        "Lux"
    ],
    "4100": [
        "CO2",
        "ppm"
    ],
    "4101": [
        "Barometric Pressure",
        "Pa"
    ],
    "4102": [
        "Soil Temperature",
        "℃"
    ],
    "4103": [
        "Soil Moisture",
        "%"
    ],
    "4104": [
        "Wind Direction",
        "°"
    ],
    "4105": [
        "Wind Speed",
        "m/s"
    ],
    "4106": [
        "pH",
        "PH"
    ],
    "4107": [
        "Light Quantum",
        "umol/㎡s"
    ],
    "4108": [
        "Electrical Conductivity",
        "mS/cm"
    ],
    "4109": [
        "Dissolved Oxygen",
        "mg/L"
    ],
    "4110": [
        "Soil Volumetric Water Content",
        "%"
    ],
    "4111": [
        "Soil Electrical Conductivity",
        "mS/cm"
    ],
    "4112": [
        "Soil Temperature(Soil Temperature, VWC & EC Sensor)",
        "℃"
    ],
    "4113": [
        "Rainfall Hourly",
        "mm/hour"
    ],
    "4115": [
        "Distance",
        "cm"
    ],
    "4116": [
        "Water Leak",
        ""
    ],
    "4117": [
        "Liguid Level",
        "cm"
    ],
    "4118": [
        "NH3",
        "ppm"
    ],
    "4119": [
        "H2S",
        "ppm"
    ],
    "4120": [
        "Flow Rate",
        "m3/h"
    ],
    "4121": [
        "Total Flow",
        "m3"
    ],
    "4122": [
        "Oxygen Concentration",
        "%vol"
    ],
    "4123": [
        "Water Eletrical Conductivity",
        "us/cm"
    ],
    "4124": [
        "Water Temperature",
        "℃"
    ],
    "4125": [
        "Soil Heat Flux",
        "W/㎡"
    ],
    "4126": [
        "Sunshine Duration",
        "h"
    ],
    "4127": [
        "Total Solar Radiation",
        "W/㎡"
    ],
    "4128": [
        "Water Surface Evaporation",
        "mm"
    ],
    "4129": [
        "Photosynthetically Active Radiation(PAR)",
        "umol/㎡s"
    ],
    "4130": [
        "Accelerometer",
        "m/s"
    ],
    "4131": [
        "Sound Intensity",
        " "
    ],
    "4133": [
        "Soil Tension",
        "KPA"
    ],
    "4134": [
        "Salinity",
        "mg/L"
    ],
    "4135": [
        "TDS",
        "mg/L"
    ],
    "4136": [
        "Leaf Temperature",
        "℃"
    ],
    "4137": [
        "Leaf Wetness",
        "%"
    ],
    "4138": [
        "Soil Moisture-10cm",
        "%"
    ],
    "4139": [
        "Soil Moisture-20cm",
        "%"
    ],
    "4140": [
        "Soil Moisture-30cm",
        "%"
    ],
    "4141": [
        "Soil Moisture-40cm",
        "%"
    ],
    "4142": [
        "Soil Temperature-10cm",
        "℃"
    ],
    "4143": [
        "Soil Temperature-20cm",
        "℃"
    ],
    "4144": [
        "Soil Temperature-30cm",
        "℃"
    ],
    "4145": [
        "Soil Temperature-40cm",
        "℃"
    ],
    "4146": [
        "PM2.5",
        "μg/m3"
    ],
    "4147": [
        "PM10",
        "μg/m3"
    ],
    "4148": [
        "Noise",
        "dB"
    ],
    "4150": [
        "AccelerometerX",
        "m/s²"
    ],
    "4151": [
        "AccelerometerY",
        "m/s²"
    ],
    "4152": [
        "AccelerometerZ",
        "m/s²"
    ],
    "4154": [
        "Salinity",
        "PSU"
    ],
    "4155": [
        "ORP",
        "mV"
    ],
    "4156": [
        "Turbidity",
        "NTU"
    ],
    "4157": [
        "Ammonia ion",
        "mg/L"
    ],
    "4158": [
        "Eletrical Conductivity",
        "mS/cm"
    ],
    "4159": [
        "Eletrical Conductivity",
        "mS/cm"
    ],
    "4160": [
        "Eletrical Conductivity",
        "mS/cm"
    ],
    "4161": [
        "Eletrical Conductivity",
        "mS/cm"
    ],
    "4162": [
        "N Content",
        "mg/kg"
    ],
    "4163": [
        "P Content",
        "mg/kg"
    ],
    "4164": [
        "K Content",
        "mg/kg"
    ],
    "4165": [
        "Measurement1",
        " "
    ],
    "4166": [
        "Measurement2",
        " "
    ],
    "4167": [
        "Measurement3",
        " "
    ],
    "4168": [
        "Measurement4",
        " "
    ],
    "4169": [
        "Measurement5",
        " "
    ],
    "4170": [
        "Measurement6",
        " "
    ],
    "4171": [
        "Measurement7",
        " "
    ],
    "4172": [
        "Measurement8",
        " "
    ],
    "4173": [
        "Measurement9",
        " "
    ],
    "4174": [
        "Measurement10",
        " "
    ],
    "4175": [
        "AI Detection No.01",
        " "
    ],
    "4176": [
        "AI Detection No.02",
        " "
    ],
    "4177": [
        "AI Detection No.03",
        " "
    ],
    "4178": [
        "AI Detection No.04",
        " "
    ],
    "4179": [
        "AI Detection No.05",
        " "
    ],
    "4180": [
        "AI Detection No.06",
        " "
    ],
    "4181": [
        "AI Detection No.07",
        " "
    ],
    "4182": [
        "AI Detection No.08",
        " "
    ],
    "4183": [
        "AI Detection No.09",
        " "
    ],
    "4184": [
        "AI Detection No.10",
        " "
    ],
    "4190": [
        "UV Index",
        " "
    ],
    "4191": [
        "Peak Wind Gust",
        "m/s"
    ],
    "4192": [
        "Sound Intensity",
        "dB"
    ],
    "4193": [
        "Light Intensity",
        " "
    ],
    "4195": [
        "TVOC",
        " ppb"
    ],
    "4196": [
        "Soil moisture intensity",
        " "
    ],
    "4197": [
        "longitude",
        "°"
    ],
    "4198": [
        "latitude",
        "°"
    ],
    "4199": [
        "Light",
        "%"
    ],
    "4200": [
        "SOS Event",
        " "
    ],
    "4201": [
        "Ultraviolet Radiation",
        "W/㎡"
    ],
    "4202": [
        "Dew point temperature",
        "℃"
    ],
    "4203": [
        "Temperature",
        "℃"
    ],
    "4204": [
        "Soil Pore Water Eletrical Conductivity",
        "mS/cm"
    ],
    "4205": [
        "Epsilon",
        " "
    ],
    "4206": [
        "VOC_INDEX",
        " "
    ],
    "4207": [
        "Noise",
        " "
    ],
    "4208": [
        "Custom event",
        " "
    ],
    "5001": [
        "Wi-Fi MAC Address",
        " "
    ],
    "5002": [
        "Bluetooth Beacon MAC Address",
        " "
    ],
    "5100": [
        "Switch",
        ""
    ]
}