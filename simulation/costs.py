import pandas as pd

from simulation.constants import InsulationSegment

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
