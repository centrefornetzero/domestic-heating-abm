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
    OWNER_OCCUPIED = 0
    RENTED_PRIVATE = 1
    RENTED_SOCIAL = 2


class EPCRating(enum.Enum):
    G = 0
    F = 1
    E = 2
    D = 3
    C = 4
    B = 5
    A = 6


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

# If a ban is active and has been announced, irrespective of the `SIGMOID_{K, OFFSET}` values,
# all agents will not consider banned heating systems after this time
MAX_BAN_LEAD_TIME_YEARS = 10
SIGMOID_K = 1
SIGMOID_OFFSET = 7


class ConstructionYearBand(enum.Enum):
    # These categories match the England & Wales EPC categories
    BUILT_PRE_1900 = 0
    BUILT_1900_1929 = 1
    BUILT_1930_1949 = 2
    BUILT_1950_1966 = 3
    BUILT_1967_1975 = 4
    BUILT_1976_1982 = 5
    BUILT_1983_1990 = 6
    BUILT_1991_1995 = 7
    BUILT_1996_2002 = 8
    BUILT_2003_2006 = 9
    BUILT_2007_ONWARDS = 10


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

# The likelihoods of houses under renovation choosing to address heating system and/or insulation as part of project
# Derived from the VERD Project, 2012-2013. UK Data Service. SN: 7773, http://doi.org/10.5255/UKDA-SN-7773-1
# Based upon the choices of houses in 'Stage 3' - finalising or actively renovating
RENO_PROBA_HEATING_SYSTEM_UPDATE = 0.18
RENO_PROBA_INSULATION_UPDATE = 0.33

# Likelihood of upgrading 1,2 or 3 insulation elements during a renovation
# Derived from the VERD Project, 2012-2013. UK Data Service. SN: 7773, http://doi.org/10.5255/UKDA-SN-7773-1
# Based upon the choices of houses in 'Stage 3' - finalising or actively renovating
RENO_NUM_INSULATION_ELEMENTS_UPGRADED = {1: 0.76, 2: 0.17, 3: 0.07}

# An amount a house may set aside for work related to home heating and energy efficiency
# Expressed as a proportion of their total renovation budget (20%)
HEATING_PROPORTION_OF_RENO_BUDGET = 0.2

# Upper bound on floor area sqm for to be classed as 'Small', by property type / built form
# As per the segmentation used in Source: BEIS - WHAT DOES IT COST TO RETROFIT HOMES?
RETROFIT_COSTS_SMALL_PROPERTY_SQM_LIMIT = {
    "FLAT": 54,
    "MID_TERRACE_HOUSE": 76,
    "SEMI_OR_END_TERRACE_HOUSE": 80,
    "SMALL_DETACHED_HOUSE": 117,
}

# Floor area of homes in England and Wales
# Source: England/Wales Energy Performance Certificates
FLOOR_AREA_SQM_33RD_PERCENTILE = 66
FLOOR_AREA_SQM_66TH_PERCENTILE = 89


class InterventionType(enum.Enum):
    RHI = 0
    BOILER_UPGRADE_SCHEME = 1
    GAS_OIL_BOILER_BAN = 2


# Source: https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/families/datasets/householdsbytypeofhouseholdandfamilyregionsofenglandandukconstituentcountries
ENGLAND_WALES_HOUSEHOLD_COUNT_2020 = 24_600_000
UK_HOUSEHOLD_COUNT = 27_800_000

# Source - https://www.heatpumps.org.uk/wp-content/uploads/2020/06/Building-the-Installer-Base-for-Net-Zero-Heating_02.06.pdf
# UK figures are proportionally scaled for England + Wales only
HEAT_PUMP_INSTALLER_COUNT = int(
    3_200 * (ENGLAND_WALES_HOUSEHOLD_COUNT_2020 / UK_HOUSEHOLD_COUNT)
)

# Source - https://www.heatpumps.org.uk/wp-content/uploads/2020/06/Building-the-Installer-Base-for-Net-Zero-Heating_02.06.pdf
# Uses the CCC Balanced Pathway scenario of 625k HPs/year in 2028, stating it requires 33,700 installers - i.e. an installation takes ~20 days
HEAT_PUMP_INSTALLATION_DURATION_MONTHS = 0.65

# Source: https://ukerc.ac.uk/news/heating-engineers-skills-and-heat-decarbonisation/
# Assuming a 1:1 replacement of gas engineer to heat pump engineers
# In 2019, 130K heating engineers registered with Gas Safe; 27.8mil households = ~215 households to every installer
HOUSEHOLDS_PER_HEAT_PUMP_INSTALLER_FLOOR = 215
