import datetime
import random
from typing import Iterator, List, Optional, Set

import pandas as pd

from abm import AgentBasedModel, UnorderedSpace
from simulation.agents import Household
from simulation.collectors import get_agent_collectors, get_model_collectors
from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    ConstructionYearBand,
    EPCRating,
    HeatingFuel,
    HeatingSystem,
    InterventionType,
    OccupantType,
    PropertyType,
)


class DomesticHeatingABM(AgentBasedModel):
    def __init__(
        self,
        start_datetime: datetime.datetime,
        step_interval: int,
        annual_renovation_rate: float,
        household_num_lookahead_years: int,
        heating_system_hassle_factor: float,
        interventions: Optional[List[InterventionType]],
        air_source_heat_pump_discount_factor_2022: float,
        gas_oil_boiler_ban_datetime: datetime.datetime,
        price_gbp_per_kwh_gas: float,
        price_gbp_per_kwh_electricity: float,
        price_gbp_per_kwh_oil: float,
    ):
        self.start_datetime = start_datetime
        self.step_interval = step_interval
        self.current_datetime = start_datetime
        self.annual_renovation_rate = annual_renovation_rate
        self.household_num_lookahead_years = household_num_lookahead_years
        self.heating_system_hassle_factor = heating_system_hassle_factor
        self.interventions = interventions or []
        self.air_source_heat_pump_discount_factor_2022 = (
            air_source_heat_pump_discount_factor_2022
        )
        self.boiler_upgrade_scheme_cumulative_spend_gbp = 0
        self.gas_oil_boiler_ban_datetime = gas_oil_boiler_ban_datetime
        self.fuel_price_gbp_per_kwh = {
            HeatingFuel.GAS: price_gbp_per_kwh_gas,
            HeatingFuel.ELECTRICITY: price_gbp_per_kwh_electricity,
            HeatingFuel.OIL: price_gbp_per_kwh_oil,
        }

        super().__init__(UnorderedSpace())

    @property
    def heating_systems(self) -> Set[HeatingSystem]:

        if InterventionType.GAS_OIL_BOILER_BAN in self.interventions:
            if self.current_datetime > self.gas_oil_boiler_ban_datetime:
                return set(HeatingSystem).difference(
                    [HeatingSystem.BOILER_GAS, HeatingSystem.BOILER_OIL]
                )
        return set(HeatingSystem)

    @property
    def air_source_heat_pump_discount_factor(self) -> float:

        if self.current_datetime.year < 2022:
            return 1
        if self.current_datetime.year > 2022:
            return 1 - self.air_source_heat_pump_discount_factor_2022
        else:
            month = self.current_datetime.month
            return 1 - (month / 12 * self.air_source_heat_pump_discount_factor_2022)

    @property
    def boiler_upgrade_scheme_spend_gbp(self) -> int:
        return sum(
            [
                agent.boiler_upgrade_grant_used
                for agent in self.space.agents
                if isinstance(agent, Household)
            ]
        )

    def increment_timestep(self):
        self.current_datetime += self.step_interval
        self.boiler_upgrade_scheme_cumulative_spend_gbp += (
            self.boiler_upgrade_scheme_spend_gbp
        )


def create_household_agents(
    household_population: pd.DataFrame,
    heat_pump_awareness: float,
    simulation_start_datetime: datetime.datetime,
    all_agents_heat_pump_suitable: bool,
) -> Iterator[Household]:
    for household in household_population.itertuples():
        yield Household(
            id=household.id,
            location=household.location,
            property_value_gbp=household.property_value_gbp,
            total_floor_area_m2=household.total_floor_area_m2,
            is_off_gas_grid=household.is_off_gas_grid,
            construction_year_band=ConstructionYearBand[
                household.construction_year_band.upper()
            ]
            if household.construction_year_band
            else None,
            property_type=PropertyType[household.property_type.upper()],
            built_form=BuiltForm[household.built_form.upper()],
            heating_system=HeatingSystem[household.heating_system.upper()],
            heating_system_install_date=simulation_start_datetime.date()
            - datetime.timedelta(
                days=random.randint(0, 365 * HEATING_SYSTEM_LIFETIME_YEARS)
            ),
            epc_rating=EPCRating[household.epc_rating.upper()],
            potential_epc_rating=EPCRating[household.potential_epc_rating.upper()],
            occupant_type=OccupantType[household.occupant_type.upper()],
            is_solid_wall=household.is_solid_wall,
            walls_energy_efficiency=household.walls_energy_efficiency,
            windows_energy_efficiency=household.windows_energy_efficiency,
            roof_energy_efficiency=household.roof_energy_efficiency,
            is_heat_pump_suitable_archetype=True
            if all_agents_heat_pump_suitable
            else household.is_heat_pump_suitable_archetype,
            is_heat_pump_aware=random.random() < heat_pump_awareness,
        )


def create_and_run_simulation(
    start_datetime: datetime.datetime,
    step_interval: datetime.timedelta,
    time_steps: int,
    household_population: pd.DataFrame,
    heat_pump_awareness: float,
    annual_renovation_rate: float,
    household_num_lookahead_years: int,
    heating_system_hassle_factor: float,
    interventions: Optional[List[InterventionType]],
    air_source_heat_pump_discount_factor_2022: float,
    all_agents_heat_pump_suitable: bool,
    gas_oil_boiler_ban_datetime: datetime.datetime,
    price_gbp_per_kwh_gas: float,
    price_gbp_per_kwh_electricity: float,
    price_gbp_per_kwh_oil: float,
):

    model = DomesticHeatingABM(
        start_datetime=start_datetime,
        step_interval=step_interval,
        annual_renovation_rate=annual_renovation_rate,
        household_num_lookahead_years=household_num_lookahead_years,
        heating_system_hassle_factor=heating_system_hassle_factor,
        interventions=interventions,
        air_source_heat_pump_discount_factor_2022=air_source_heat_pump_discount_factor_2022,
        gas_oil_boiler_ban_datetime=gas_oil_boiler_ban_datetime,
        price_gbp_per_kwh_gas=price_gbp_per_kwh_gas,
        price_gbp_per_kwh_electricity=price_gbp_per_kwh_electricity,
        price_gbp_per_kwh_oil=price_gbp_per_kwh_oil,
    )

    households = create_household_agents(
        household_population,
        heat_pump_awareness,
        model.start_datetime,
        all_agents_heat_pump_suitable,
    )
    model.add_agents(households)

    agent_collectors = get_agent_collectors(model)
    model_collectors = get_model_collectors(model)

    return model.run(time_steps, agent_collectors, model_collectors)
