import random

import pandas as pd

from abm import Agent
from simulation.constants import (
    HEATING_SYSTEM_FUEL,
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    Epc,
    HeatingFuel,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.settings import HEAT_PUMP_AWARENESS


class Household(Agent):
    def __init__(
        self,
        location: str,
        property_value: int,
        floor_area_sqm: int,
        off_gas_grid: bool,
        construction_year_band: pd.Interval,
        property_type: PropertyType,
        built_form: BuiltForm,
        heating_system: HeatingSystem,
        epc: Epc,
        occupant_type: OccupantType,
        is_solid_wall: bool,
        walls_energy_efficiency: int,
        windows_energy_efficiency: int,
        roof_energy_efficiency: int,
        is_heat_pump_suitable_archetype: bool,
    ):
        # Property / tenure attributes
        self.location = location
        self.property_type = property_type
        self.occupant_type = occupant_type
        self.built_form = built_form
        self.floor_area_sqm = floor_area_sqm
        self.property_value = property_value
        self.is_solid_wall = is_solid_wall
        self.construction_year = self.sample_uniformly_from_interval(
            construction_year_band.left, construction_year_band.right
        )
        self.is_heat_pump_suitable_archetype = is_heat_pump_suitable_archetype

        # Heating / energy performance attributes
        self.off_gas_grid = off_gas_grid
        self.heating_functioning = True
        self.heating_system = heating_system
        self.heating_system_age = random.randint(0, HEATING_SYSTEM_LIFETIME_YEARS)
        self.epc = epc
        self.walls_energy_efficiency = walls_energy_efficiency
        self.roof_energy_efficiency = roof_energy_efficiency
        self.windows_energy_efficiency = windows_energy_efficiency
        self.is_heat_pump_aware = random.random() < HEAT_PUMP_AWARENESS

    @staticmethod
    def sample_uniformly_from_interval(
        lower_bound: int,
        upper_bound: int,
    ) -> float:
        return random.uniform(lower_bound, upper_bound)

    @property
    def heating_fuel(self) -> HeatingFuel:
        return HEATING_SYSTEM_FUEL[self.heating_system]

    def step(self, model):
        pass
