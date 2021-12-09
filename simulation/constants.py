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
HAZARD_RATE_HEATING_SYSTEM_ALPHA = 6
HAZARD_RATE_HEATING_SYSTEM_BETA = 15


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


class InsulationSegment(enum.Enum):
    SMALL_FLAT = 0
    LARGE_FLAT = 1
    SMALL_MID_TERRACE_HOUSE = 2
    LARGE_MID_TERRACE_HOUSE = 3
    SMALL_SEMI_END_TERRACE_HOUSE = 4
    LARGE_SEMI_END_TERRACE_HOUSE = 5
    SMALL_DETACHED_HOUSE = 6
    LARGE_DETACHED_HOUSE = 7
    BUNGALOW = 8


# parameters chosen to align to a distribution of discount rates obtained from an investigation of 1,217 random
# U.S. homeowners given choice experiments relating to the purchase of a water heater (mean 19%; std. 23%)
# Individual Time Preferences and Energy Efficiency (NBER Working Paper No. 20969)
DISCOUNT_RATE_WEIBULL_ALPHA = 0.8
DISCOUNT_RATE_WEIBULL_BETA = 0.165


class EventTrigger(enum.Enum):
    BREAKDOWN = 0
    RENOVATION = 1
    EPC_C_UPGRADE = 2


# Scale factor is inferred from general relationship between estimated floor area and kW capacity
# https://www.boilerguide.co.uk/articles/size-heat-pump-need (see table)
# https://www.imsheatpumps.co.uk/blog/what-size-heat-pump-do-i-need-for-my-house/
# https://www.homeheatingguide.co.uk/renewables-advice/air-source-heat-pumps-a-sizing-guide
HEAT_PUMP_CAPACITY_SCALE_FACTOR = {
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 0.1,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 0.08,
}

MAX_HEAT_PUMP_CAPACITY_KW = {
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 20.0,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 25.0,
}

MIN_HEAT_PUMP_CAPACITY_KW = {
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 4.0,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 4.0,
}


class PropertySize(enum.Enum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


# Source: https://www.ovoenergy.com/guides/energy-guides/how-much-heating-energy-do-you-use
# Assume figure of 133kWh/m2a a reflects an average heating system Coefficient of Performance of 0.92 (gas boiler)
# 133 * 0.92 = 122kWh/m2a
HEATING_KWH_PER_SQM_ANNUAL = 122

FUEL_KWH_TO_HEAT_KWH: Dict[HeatingSystem, float] = {
    # The conversion factor between 1kWh of fuel and useful heat. For example:
    # Gas Boilers ~ 0.9, since 1kWh of gas produces ~0.9kWh of heat (due to inefficiencies in the boiler)
    HeatingSystem.BOILER_GAS: 0.92,
    HeatingSystem.BOILER_OIL: 0.92,
    HeatingSystem.BOILER_ELECTRIC: 0.995,
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 3,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 4,
}

HEAT_PUMPS = {HeatingSystem.HEAT_PUMP_AIR_SOURCE, HeatingSystem.HEAT_PUMP_GROUND_SOURCE}

BOILERS = {
    HeatingSystem.BOILER_GAS,
    HeatingSystem.BOILER_OIL,
    HeatingSystem.BOILER_ELECTRIC,
}
