import datetime
import math
import random

from abm import Agent
from simulation.constants import (
    GB_PROPERTY_VALUE_WEIBULL_ALPHA,
    GB_PROPERTY_VALUE_WEIBULL_BETA,
    GB_RENOVATION_BUDGET_WEIBULL_ALPHA,
    GB_RENOVATION_BUDGET_WEIBULL_BETA,
    HEATING_SYSTEM_FUEL,
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingFuel,
    HeatingSystem,
    OccupantType,
    PropertyType,
)


class Household(Agent):
    def __init__(
        self,
        location: str,
        property_value: int,
        floor_area_sqm: int,
        off_gas_grid: bool,
        construction_year_band: ConstructionYearBand,
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
        is_heat_pump_aware: bool,
    ):
        # Property / tenure attributes
        self.location = location
        self.property_type = property_type
        self.occupant_type = occupant_type
        self.built_form = built_form
        self.floor_area_sqm = floor_area_sqm
        self.property_value = property_value
        self.is_solid_wall = is_solid_wall
        self.construction_year_band = construction_year_band
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
        self.is_heat_pump_aware = is_heat_pump_aware

        # Renovation attributes
        self.is_renovating = False

    @property
    def heating_fuel(self) -> HeatingFuel:
        return HEATING_SYSTEM_FUEL[self.heating_system]

    @staticmethod
    def get_weibull_percentile_from_value(
        alpha: float, beta: float, input_value: float
    ) -> float:

        return 1 - math.exp(-((input_value / beta) ** alpha))

    @staticmethod
    def get_weibull_value_from_percentile(
        alpha: float, beta: float, percentile: float
    ) -> float:

        epsilon = 0.0000001
        return beta * (-math.log(1 + epsilon - percentile)) ** (1 / alpha)

    @staticmethod
    def evaluate_trial(p: float) -> bool:
        return random.random() < p

    @property
    def wealth_percentile(self) -> float:

        return self.get_weibull_percentile_from_value(
            GB_PROPERTY_VALUE_WEIBULL_ALPHA,
            GB_PROPERTY_VALUE_WEIBULL_BETA,
            self.property_value,
        )

    @property
    def renovation_budget(self) -> float:
        # An amount a house may set aside for work related to home heating and energy efficiency
        # Expressed as a proportion of their total renovation budget (10%)

        HEATING_PROPORTION_OF_BUDGET = 0.1

        return HEATING_PROPORTION_OF_BUDGET * self.get_weibull_value_from_percentile(
            GB_RENOVATION_BUDGET_WEIBULL_ALPHA,
            GB_RENOVATION_BUDGET_WEIBULL_BETA,
            self.wealth_percentile,
        )

    def evaluate_renovation(self, model) -> None:

        step_interval_years = model.step_interval / datetime.timedelta(days=365)
        proba_renovate = model.annual_renovation_rate * step_interval_years

        self.is_renovating = self.evaluate_trial(proba_renovate)

    def decide_renovation_scope(self) -> None:

        # Derived from the VERD Project, 2012-2013. UK Data Service. SN: 7773, http://doi.org/10.5255/UKDA-SN-7773-1
        # Based upon the choices of houses in 'Stage 3' - finalising or actively renovating
        PROBA_HEATING_SYSTEM_UPDATE = 0.18
        PROBA_INSULATION_UPDATE = 0.33

        self.renovate_heating_system = self.evaluate_trial(PROBA_HEATING_SYSTEM_UPDATE)
        self.renovate_insulation = self.evaluate_trial(PROBA_INSULATION_UPDATE)

    def step(self, model):
        self.evaluate_renovation(model)
        if self.is_renovating:
            self.decide_renovation_scope()
