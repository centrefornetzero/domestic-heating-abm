import datetime
import random
from typing import TYPE_CHECKING, Dict

import pandas as pd

from simulation.constants import (
    ENGLAND_WALES_HOUSEHOLD_COUNT_2020,
    FUEL_KWH_TO_HEAT_KWH,
    HEATING_SYSTEM_FUEL,
    HeatingSystem,
    InsulationSegment,
    PropertySize,
)

if TYPE_CHECKING:
    from simulation.agents import Household
    from simulation.model import DomesticHeatingABM

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
    # These values incorporate installation costs
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
    # These values incorporate installation costs
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

BOILER_INSTALLATION_COST_GBP = 1_000

MEAN_COST_GBP_BOILER_GAS: Dict[PropertySize, int] = {
    # Source: https://www.boilerguide.co.uk/articles/what-size-boiler-needed
    PropertySize.SMALL: 2277 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.MEDIUM: 2347 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.LARGE: 2476 + BOILER_INSTALLATION_COST_GBP,
}

MEAN_COST_GBP_BOILER_OIL: Dict[PropertySize, int] = {
    # Source: https://www.theecoexperts.co.uk/boilers/oil-boiler
    # Adjusted for monotonicity - cost at each property size >= highest trailing value
    PropertySize.SMALL: 2350 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.MEDIUM: 2350 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.LARGE: 3025 + BOILER_INSTALLATION_COST_GBP,
}

MEAN_COST_GBP_BOILER_ELECTRIC: Dict[PropertySize, int] = {
    # Source: https://www.boilerguide.co.uk/articles/best-electric-boilers
    PropertySize.SMALL: 1250 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.MEDIUM: 1750 + BOILER_INSTALLATION_COST_GBP,
    PropertySize.LARGE: 2250 + BOILER_INSTALLATION_COST_GBP,
}

# SOURCE: https://webarchive.nationalarchives.gov.uk/ukgwa/20121205193015/http:/www.decc.gov.uk/assets/decc/what%20we%20do/uk%20energy%20supply/energy%20mix/distributed%20energy%20heat/1467-potential-costs-district-heating-network.pdf
# "First-time" installation costs (e.g. pipework, radiator upgrades, boreholes) are approximately 10% of total costs for ASHP, and 50% of total costs of a GSHP
HEAT_PUMP_AIR_SOURCE_REINSTALL_DISCOUNT = 0.1
HEAT_PUMP_GROUND_SOURCE_REINSTALL_DISCOUNT = 0.5


def get_unit_and_install_costs(
    household: "Household",
    heating_system: HeatingSystem,
    model: "DomesticHeatingABM",
) -> int:

    costs = 0
    # Any projected heat pump discounts are capped at the price of a gas boiler for a household
    heat_pump_price_floor = MEAN_COST_GBP_BOILER_GAS[household.property_size]

    if heating_system != household.heating_system:
        decommissioning_costs = random.randint(500, 2_000)
        costs += decommissioning_costs

    if heating_system == HeatingSystem.HEAT_PUMP_AIR_SOURCE:
        kw_capacity = household.compute_heat_pump_capacity_kw(heating_system)
        unit_and_install_costs = MEDIAN_COST_GBP_HEAT_PUMP_AIR_SOURCE[kw_capacity] * (
            1 - model.air_source_heat_pump_discount_factor
        )

        if household.heating_system == HeatingSystem.HEAT_PUMP_AIR_SOURCE:
            # Some installation work required to install a heat pump first time does not apply to 2nd+ installations
            unit_and_install_costs *= 1 - HEAT_PUMP_AIR_SOURCE_REINSTALL_DISCOUNT

        costs += max(unit_and_install_costs, heat_pump_price_floor)

    if heating_system == HeatingSystem.HEAT_PUMP_GROUND_SOURCE:
        kw_capacity = household.compute_heat_pump_capacity_kw(heating_system)
        unit_and_install_costs = MEDIAN_COST_GBP_HEAT_PUMP_GROUND_SOURCE[kw_capacity]

        if household.heating_system == HeatingSystem.HEAT_PUMP_GROUND_SOURCE:
            # Some installation work required to install a heat pump first time does not apply to 2nd+ installations
            unit_and_install_costs *= 1 - HEAT_PUMP_GROUND_SOURCE_REINSTALL_DISCOUNT

        costs += max(unit_and_install_costs, heat_pump_price_floor)

    if heating_system == HeatingSystem.BOILER_GAS:
        costs += MEAN_COST_GBP_BOILER_GAS[household.property_size]

    if heating_system == HeatingSystem.BOILER_OIL:
        costs += MEAN_COST_GBP_BOILER_OIL[household.property_size]

    if heating_system == HeatingSystem.BOILER_ELECTRIC:
        costs += MEAN_COST_GBP_BOILER_ELECTRIC[household.property_size]

    return int(costs)


def discount_annual_cash_flow(
    discount_rate: float, cashflow_gbp: int, duration_years: int
) -> float:

    return sum([cashflow_gbp / (1 + discount_rate) ** t for t in range(duration_years)])


def get_heating_fuel_costs_net_present_value(
    household: "Household",
    heating_system: HeatingSystem,
    model: "DomesticHeatingABM",
):

    SCALE_FACTOR_COP = (
        FUEL_KWH_TO_HEAT_KWH[household.heating_system]
        / FUEL_KWH_TO_HEAT_KWH[heating_system]
    )
    annual_heating_demand_kwh = household.annual_kwh_heating_demand * SCALE_FACTOR_COP
    annual_heating_bill = (
        annual_heating_demand_kwh
        * model.fuel_price_gbp_per_kwh[HEATING_SYSTEM_FUEL[heating_system]]
    )

    return discount_annual_cash_flow(
        household.discount_rate,
        annual_heating_bill,
        model.household_num_lookahead_years,
    )


RHI_TARIFF_GBP_PER_KWH = {
    # Source: Ofgem
    # https://www.ofgem.gov.uk/publications/domestic-rhi-tariff-table-2021-2022
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 0.1092,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 0.2129,
}

RHI_HEAT_DEMAND_LIMIT_KWH = {
    # Source: Ofgem
    # https://www.ofgem.gov.uk/publications/factsheet-tariffs-and-payments-domestic-rhi
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: 20_000,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: 30_000,
}


def estimate_rhi_annual_payment(
    household: "Household",
    heating_system: HeatingSystem,
    rhi_tariff_gbp_per_kwh: Dict[HeatingSystem, float] = RHI_TARIFF_GBP_PER_KWH,
    rhi_heat_demand_limit_kwh: Dict[HeatingSystem, int] = RHI_HEAT_DEMAND_LIMIT_KWH,
) -> int:
    """
    Example:
    The eligible heat will be worked out using the following method:
    Establish total annual heating + hot water demand, e.g. 25,000kWh/yr.
    Calculate the electrical energy the system will consume: e.g. 25,000 / COP = 7353kWh/yr.
    Deduct from total annual demand for the ‘renewable’ content: e.g. 25,000 – 7353 = 17,647kWh/yr.
    Multiply by RHI tariff (e.g. 20.46p/kWh) to get annual RHI payment: 17,647 x £0.193 = £3,599 per year
    """

    if heating_system not in [
        HeatingSystem.HEAT_PUMP_AIR_SOURCE,
        HeatingSystem.HEAT_PUMP_GROUND_SOURCE,
    ]:
        return 0

    SCALE_FACTOR_COP = (
        FUEL_KWH_TO_HEAT_KWH[household.heating_system]
        / FUEL_KWH_TO_HEAT_KWH[heating_system]
    )

    annual_heat_kwh_proposed = household.annual_kwh_heating_demand * SCALE_FACTOR_COP
    annual_heat_kwh_delta = (
        household.annual_kwh_heating_demand - annual_heat_kwh_proposed
    )

    rhi_kwh_cap = rhi_heat_demand_limit_kwh[heating_system]

    annual_heat_kwh_delta_capped = (
        rhi_kwh_cap
        if annual_heat_kwh_delta > rhi_kwh_cap
        else 0
        if annual_heat_kwh_delta < 0
        else annual_heat_kwh_delta
    )

    rhi_annual_payment_gbp = int(
        annual_heat_kwh_delta_capped * rhi_tariff_gbp_per_kwh[heating_system]
    )

    return rhi_annual_payment_gbp


def estimate_boiler_upgrade_scheme_grant(
    heating_system: HeatingSystem,
    model: "DomesticHeatingABM",
):

    if heating_system not in [
        HeatingSystem.HEAT_PUMP_AIR_SOURCE,
        HeatingSystem.HEAT_PUMP_GROUND_SOURCE,
    ]:
        return 0

    model_population_scale = ENGLAND_WALES_HOUSEHOLD_COUNT_2020 / model.household_count
    boiler_upgrade_funding_cap_gbp = 450_000_000 / model_population_scale
    if (
        model.boiler_upgrade_scheme_cumulative_spend_gbp
        >= boiler_upgrade_funding_cap_gbp
    ):
        return 0

    if (
        not datetime.date(2022, 4, 1)
        <= model.current_datetime.date()
        < datetime.date(2025, 4, 1)
    ):
        return 0

    if heating_system == HeatingSystem.HEAT_PUMP_AIR_SOURCE:
        return 5_000

    if heating_system == HeatingSystem.HEAT_PUMP_GROUND_SOURCE:
        return 6_000
