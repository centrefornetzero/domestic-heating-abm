import datetime
import random
from typing import Iterator

import pandas as pd

from abm import AgentBasedModel, UnorderedSpace
from simulation.agents import Household
from simulation.collectors import get_agent_collectors, model_collectors
from simulation.constants import (
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingSystem,
    OccupantType,
    PropertyType,
)


class CnzAgentBasedModel(AgentBasedModel):
    def __init__(
        self,
        start_datetime,
        step_interval,
        annual_renovation_rate,
    ):
        self.start_datetime = start_datetime
        self.step_interval = step_interval
        self.current_datetime = start_datetime
        self.annual_renovation_rate = annual_renovation_rate

        super().__init__(UnorderedSpace())

    def step(self):
        self.current_datetime += self.step_interval


def create_households(
    num_households: int,
    household_distribution: pd.DataFrame,
    heat_pump_awareness: float,
) -> Iterator[Household]:

    households = household_distribution.sample(num_households, replace=True)
    for household in households.itertuples():
        yield Household(
            location=household.location,
            property_value=household.property_value,
            floor_area_sqm=household.floor_area_sqm,
            off_gas_grid=household.off_gas_grid,
            construction_year_band=ConstructionYearBand[
                household.construction_year_band.upper()
            ],
            property_type=PropertyType[household.property_type.upper()],
            built_form=BuiltForm[household.built_form.upper()],
            heating_system=HeatingSystem[household.heating_system.upper()],
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
    num_steps: int,
    num_households: int,
    household_distribution: pd.DataFrame,
    heat_pump_awareness: float,
    annual_renovation_rate: float,
):
    model = CnzAgentBasedModel(
        start_datetime=start_datetime,
        step_interval=step_interval,
        annual_renovation_rate=annual_renovation_rate,
    )

    households = create_households(
        num_households, household_distribution, heat_pump_awareness
    )
    model.add_agents(households)

    agent_collectors = get_agent_collectors(model)

    return model.run(num_steps, agent_collectors, model_collectors)
