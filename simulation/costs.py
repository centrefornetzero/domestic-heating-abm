import random
from typing import Dict

import pandas as pd

from simulation.constants import HeatingSystem, InsulationSegment, PropertySize

# Source: BEIS - WHAT DOES IT COST TO RETROFIT HOMES?

CAVITY_WALL_INSULATION_COST = {
    InsulationSegment.SMALL_FLAT: pd.Interval(300, 630),
    InsulationSegment.LARGE_FLAT: pd.Interval(350, 640),
    InsulationSegment.SMALL_MID_TERRACE_HOUSE: pd.Interval(350, 640),
    InsulationSegment.LARGE_MID_TERRACE_HOUSE: pd.Interval(450, 670),
    InsulationSegment.SMALL_SEMI_END_TERRACE_HOUSE: pd.Interval(480, 660),
    InsulationSegment.LARGE_SEMI_END_TERRACE_HOUSE: pd.Interval(600, 690),
    InsulationSegment.SMALL_DETACHED_HOUSE: pd.Interval(550, 800),
    InsulationSegment.LARGE_DETACHED_HOUSE: pd.Interval(750, 1_200),
    InsulationSegment.BUNGALOW: pd.Interval(500, 650),
}

INTERNAL_WALL_INSULATION_COST = {
    InsulationSegment.SMALL_FLAT: pd.Interval(2_500, 3_000),
    InsulationSegment.LARGE_FLAT: pd.Interval(3_000, 4_000),
    InsulationSegment.SMALL_MID_TERRACE_HOUSE: pd.Interval(3_000, 5_000),
    InsulationSegment.LARGE_MID_TERRACE_HOUSE: pd.Interval(4_000, 4_000),
    InsulationSegment.SMALL_SEMI_END_TERRACE_HOUSE: pd.Interval(5_000, 10_400),
    InsulationSegment.LARGE_SEMI_END_TERRACE_HOUSE: pd.Interval(6_000, 8_000),
    InsulationSegment.SMALL_DETACHED_HOUSE: pd.Interval(6_600, 8_000),
    InsulationSegment.LARGE_DETACHED_HOUSE: pd.Interval(7_000, 11_600),
    InsulationSegment.BUNGALOW: pd.Interval(5_600, 7_000),
}

LOFT_INSULATION_JOISTS_COST = {
    InsulationSegment.SMALL_FLAT: pd.Interval(180, 580),
    InsulationSegment.LARGE_FLAT: pd.Interval(235, 590),
    InsulationSegment.SMALL_MID_TERRACE_HOUSE: pd.Interval(180, 600),
    InsulationSegment.LARGE_MID_TERRACE_HOUSE: pd.Interval(200, 645),
    InsulationSegment.SMALL_SEMI_END_TERRACE_HOUSE: pd.Interval(180, 610),
    InsulationSegment.LARGE_SEMI_END_TERRACE_HOUSE: pd.Interval(210, 650),
    InsulationSegment.SMALL_DETACHED_HOUSE: pd.Interval(220, 750),
    InsulationSegment.LARGE_DETACHED_HOUSE: pd.Interval(300, 955),
    InsulationSegment.BUNGALOW: pd.Interval(430, 900),
}

DOUBLE_GLAZING_UPVC_COST = {
    InsulationSegment.SMALL_FLAT: pd.Interval(1_200, 3_000),
    InsulationSegment.LARGE_FLAT: pd.Interval(3_000, 4_200),
    InsulationSegment.SMALL_MID_TERRACE_HOUSE: pd.Interval(3_200, 5_000),
    InsulationSegment.LARGE_MID_TERRACE_HOUSE: pd.Interval(4_800, 5_500),
    InsulationSegment.SMALL_SEMI_END_TERRACE_HOUSE: pd.Interval(4_800, 7_000),
    InsulationSegment.LARGE_SEMI_END_TERRACE_HOUSE: pd.Interval(6_000, 8_000),
    InsulationSegment.SMALL_DETACHED_HOUSE: pd.Interval(5_000, 7_000),
    InsulationSegment.LARGE_DETACHED_HOUSE: pd.Interval(7_000, 10_000),
    InsulationSegment.BUNGALOW: pd.Interval(5_800, 8_000),
}

MEDIAN_COST_GBP_HEAT_PUMP_AIR_SOURCE: Dict[int, int] = {
    # Source: RHI December 2020 Data
    # Adjusted for monotonicity: cost at each capacity >= highest trailing value
    1: 1500,
    2: 3000,
    3: 4500,
    4: 6000,
    5: 7500,
    6: 7500,
    7: 8050,
    8: 9200,
    9: 10350,
    10: 11500,
    11: 11500,
    12: 11500,
    13: 12350,
    14: 13300,
    15: 14250,
    16: 14250,
    17: 14250,
    18: 14580,
    19: 15390,
    20: 16200,
}

MEDIAN_COST_GBP_HEAT_PUMP_GROUND_SOURCE: Dict[int, int] = {
    # Adjusted for monotonicity: cost at each capacity >= highest trailing value
    1: 1800,
    2: 3600,
    3: 5400,
    4: 7200,
    5: 9000,
    6: 10920,
    7: 12740,
    8: 14560,
    9: 16380,
    10: 18200,
    11: 18200,
    12: 18840,
    13: 20410,
    14: 21980,
    15: 23550,
    16: 23550,
    17: 24990,
    18: 26460,
    19: 27930,
    20: 29400,
    21: 29400,
    22: 29400,
    23: 30590,
    24: 31920,
    25: 33250,
}

MEAN_COST_GBP_BOILER_GAS: Dict[PropertySize, int] = {
    # Source: https://www.boilerguide.co.uk/articles/what-size-boiler-needed
    PropertySize.SMALL: 2277,
    PropertySize.MEDIUM: 2347,
    PropertySize.LARGE: 2476,
}

MEAN_COST_GBP_BOILER_OIL: Dict[PropertySize, int] = {
    # Source: https://www.theecoexperts.co.uk/boilers/oil-boiler
    PropertySize.SMALL: 2350,
    PropertySize.MEDIUM: 2183,
    PropertySize.LARGE: 3025,
}

MEAN_COST_GBP_BOILER_ELECTRIC: Dict[PropertySize, int] = {
    # Source: https://www.boilerguide.co.uk/articles/best-electric-boilers
    PropertySize.SMALL: 1250,
    PropertySize.MEDIUM: 1750,
    PropertySize.LARGE: 2250,
}


def get_unit_and_install_costs(household, heating_system):

    costs = 0

    if heating_system != household.heating_system:
        decommissioning_costs = random.randint(500, 2_000)
        costs += decommissioning_costs

    if heating_system == HeatingSystem.HEAT_PUMP_AIR_SOURCE:
        kw_capacity = household.compute_heat_pump_capacity_kw(heating_system)
        costs += MEDIAN_COST_GBP_HEAT_PUMP_AIR_SOURCE[kw_capacity]

    if heating_system == HeatingSystem.HEAT_PUMP_GROUND_SOURCE:
        kw_capacity = household.compute_heat_pump_capacity_kw(heating_system)
        costs += MEDIAN_COST_GBP_HEAT_PUMP_GROUND_SOURCE[kw_capacity]

    if heating_system == HeatingSystem.BOILER_GAS:
        costs += MEAN_COST_GBP_BOILER_GAS[household.property_size]

    if heating_system == HeatingSystem.BOILER_OIL:
        costs += MEAN_COST_GBP_BOILER_OIL[household.property_size]

    if heating_system == HeatingSystem.BOILER_ELECTRIC:
        costs += MEAN_COST_GBP_BOILER_ELECTRIC[household.property_size]

    return costs
