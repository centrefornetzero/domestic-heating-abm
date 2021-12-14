import datetime
import random
from typing import Iterator

import pandas as pd

from abm import AgentBasedModel, UnorderedSpace
from simulation.agents import Household
from simulation.collectors import get_agent_collectors, model_collectors
from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingSystem,
    InterventionType,
    OccupantType,
    PropertyType,
)


class DomesticHeatingABM(AgentBasedModel):
    def __init__(
        self,
        start_datetime,
        step_interval,
        annual_renovation_rate,
        household_num_lookahead_years,
        heating_system_hassle_factor,
        intervention,
        air_source_heat_pump_discount_factor_2022,
    ):
        self.start_datetime = start_datetime
        self.step_interval = step_interval
        self.current_datetime = start_datetime
        self.annual_renovation_rate = annual_renovation_rate
        self.heating_systems = set(HeatingSystem)
        self.household_num_lookahead_years = household_num_lookahead_years
        self.heating_system_hassle_factor = heating_system_hassle_factor
        self.intervention = (
            InterventionType[intervention.upper()] if intervention else None
        )
        self.air_source_heat_pump_discount_factor_2022 = (
            air_source_heat_pump_discount_factor_2022
        )

        super().__init__(UnorderedSpace())

    @property
    def air_source_heat_pump_discount_factor(self) -> float:

        if self.current_datetime.year < 2022:
            return 1
        if self.current_datetime.year > 2022:
            return 1 - self.air_source_heat_pump_discount_factor_2022
        else:
            month = self.current_datetime.month
            return 1 - (month / 12 * self.air_source_heat_pump_discount_factor_2022)

    def increment_timestep(self):
        self.current_datetime += self.step_interval


def create_households(
    num_households: int,
    household_distribution: pd.DataFrame,
    heat_pump_awareness: float,
    simulation_start_datetime: datetime.datetime,
) -> Iterator[Household]:

    households = household_distribution.sample(num_households, replace=True)
    for household in households.itertuples():
        yield Household(
            location=household.location,
            property_value_gbp=household.property_value_gbp,
            floor_area_sqm=household.floor_area_sqm,
            off_gas_grid=household.off_gas_grid,
            construction_year_band=ConstructionYearBand[
                household.construction_year_band.upper()
            ],
            property_type=PropertyType[household.property_type.upper()],
            built_form=BuiltForm[household.built_form.upper()],
            heating_system=HeatingSystem[household.heating_system.upper()],
            heating_system_install_date=simulation_start_datetime.date()
            - datetime.timedelta(
                days=random.randint(0, 365 * HEATING_SYSTEM_LIFETIME_YEARS)
            ),
            epc=Epc[household.epc.upper()],
            potential_epc=Epc[household.potential_epc.upper()],
            occupant_type=OccupantType[household.occupant_type.upper()],
            is_solid_wall=household.is_solid_wall,
            walls_energy_efficiency=household.walls_energy_efficiency,
            windows_energy_efficiency=household.windows_energy_efficiency,
            roof_energy_efficiency=household.roof_energy_efficiency,
            is_heat_pump_suitable_archetype=household.is_heat_pump_suitable_archetype,
            is_heat_pump_aware=random.random() < heat_pump_awareness,
        )


def create_and_run_simulation(
    start_datetime: datetime.datetime,
    step_interval: datetime.timedelta,
    time_steps: int,
    num_households: int,
    household_distribution: pd.DataFrame,
    heat_pump_awareness: float,
    annual_renovation_rate: float,
    household_num_lookahead_years: int,
    heating_system_hassle_factor: float,
    intervention: str,
    air_source_heat_pump_discount_factor_2022: float,
):

    model = DomesticHeatingABM(
        start_datetime=start_datetime,
        step_interval=step_interval,
        annual_renovation_rate=annual_renovation_rate,
        household_num_lookahead_years=household_num_lookahead_years,
        heating_system_hassle_factor=heating_system_hassle_factor,
        intervention=intervention,
        air_source_heat_pump_discount_factor_2022=air_source_heat_pump_discount_factor_2022,
    )

    households = create_households(
        num_households,
        household_distribution,
        heat_pump_awareness,
        model.start_datetime,
    )
    model.add_agents(households)

    agent_collectors = get_agent_collectors(model)

    return model.run(time_steps, agent_collectors, model_collectors)
