import datetime
from collections import Counter
from typing import Dict, Iterator

import pandas as pd

from abm import AgentBasedModel, UnorderedSpace
from simulation.agents import Household
from simulation.collectors import get_agent_collectors, model_collectors
from simulation.constants import (
    BuiltForm,
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
    ):
        self.start_datetime = start_datetime
        self.step_interval = step_interval
        self.current_datetime = start_datetime

        super().__init__(UnorderedSpace())

    @property
    def current_agent_count(self) -> Dict:
        return Counter([agent.__class__ for agent in self.space.agents])

    @property
    def current_heating_system_count(self) -> Dict[HeatingSystem, int]:
        return Counter(
            [
                agent.heating_system
                for agent in self.space.agents
                if isinstance(agent, Household)
            ]
        )

    def step(self):
        if self.current_datetime == self.start_datetime:
            self.initial_heating_system_count = self.current_heating_system_count
        self.current_datetime += self.step_interval


def parse_string_interval(string_range: str) -> pd.Interval:
    min_value, max_value = [int(i) for i in string_range.split("-")]
    return pd.Interval(min_value, max_value, closed="both")


def create_households(
    num_households: int,
    household_distribution: pd.DataFrame,
) -> Iterator[Household]:
    household_distribution["construction_year_band"] = household_distribution[
        "construction_year_band"
    ].apply(parse_string_interval)

    households = household_distribution.sample(num_households, replace=True)
    for household in households.itertuples():
        yield Household(
            location=household.location,
            property_value=household.property_value,
            floor_area_sqm=household.floor_area_sqm,
            off_gas_grid=household.off_gas_grid,
            construction_year_band=household.construction_year_band,
            property_type=PropertyType[household.property_type.upper()],
            built_form=BuiltForm[household.built_form.upper()],
            heating_system=HeatingSystem[household.heating_system.upper()],
            epc=Epc[household.epc.upper()],
            occupant_type=OccupantType[household.occupant_type.upper()],
            is_solid_wall=household.is_solid_wall,
            walls_energy_efficiency=household.walls_energy_efficiency,
            windows_energy_efficiency=household.windows_energy_efficiency,
            roof_energy_efficiency=household.roof_energy_efficiency,
            is_heat_pump_suitable_archetype=household.is_heat_pump_suitable_archetype,
        )


def create_and_run_simulation(
    start_datetime: datetime.datetime,
    step_interval: datetime.timedelta,
    num_steps: int,
    num_households: int,
    household_distribution: pd.DataFrame,
):
    model = CnzAgentBasedModel(
        start_datetime=start_datetime,
        step_interval=step_interval,
    )

    households = create_households(num_households, household_distribution)
    model.add_agents(households)

    agent_collectors = get_agent_collectors(model)

    return model.run(num_steps, agent_collectors, model_collectors)
