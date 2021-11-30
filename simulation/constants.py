import enum
from typing import Dict


class PropertyType(enum.Enum):
    HOUSE = 0
    FLAT = 1
    BUNGALOW = 2


class BuiltForm(enum.Enum):
    MID_TERRACE = 0
    SEMI_DETACHED = 1
    DETACHED = 2
    END_TERRACE = 3


class OccupantType(enum.Enum):
    OWNER_OCCUPIER = 0
    RENTER_PRIVATE = 1
    RENTER_SOCIAL = 2


class Epc(enum.Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6


class HeatingSystem(enum.Enum):
    BOILER_GAS = 0
    BOILER_OIL = 1
    BOILER_ELECTRIC = 2
    HEAT_PUMP_AIR_SOURCE = 3
    HEAT_PUMP_GROUND_SOURCE = 4


class HeatingFuel(enum.Enum):
    GAS = 0
    ELECTRICITY = 1
    OIL = 2


HEATING_SYSTEM_FUEL: Dict[HeatingSystem, HeatingFuel] = {
    HeatingSystem.BOILER_GAS: HeatingFuel.GAS,
    HeatingSystem.BOILER_OIL: HeatingFuel.OIL,
    HeatingSystem.BOILER_ELECTRIC: HeatingFuel.ELECTRICITY,
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: HeatingFuel.ELECTRICITY,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: HeatingFuel.ELECTRICITY,
}

HEATING_SYSTEM_LIFETIME_YEARS = 15


class ConstructionYearBand(enum.Enum):
    BUILT_PRE_1919 = 0
    BUILT_1919_1944 = 1
    BUILT_1945_1964 = 2
    BUILT_1965_1982 = 3
    BUILT_1983_1992 = 4
    BUILT_1993_1999 = 5
    BUILT_POST_1999 = 6


# Parameters describing distributions

# A distribution matching 50th/90th percentiles from 2020 Houzz & Home report (11k/100k respectively)
# http://st.hzcdn.com/static/econ/en-GB/2020_HouzzAndHome_UK_Renovation_Trends_Study.pdf
GB_RENOVATION_BUDGET_WEIBULL_ALPHA = 0.55
GB_RENOVATION_BUDGET_WEIBULL_BETA = 21_994

# A distribution aligned to Q2 2021 GB property values
GB_PROPERTY_VALUE_WEIBULL_ALPHA = 1.61
GB_PROPERTY_VALUE_WEIBULL_BETA = 280_000


class Element(enum.Enum):
    ROOF = 0
    GLAZING = 1
    WALLS = 2
