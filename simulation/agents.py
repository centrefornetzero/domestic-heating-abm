import datetime
import math
import random
from typing import TYPE_CHECKING, Dict, Set

import pandas as pd

from abm import Agent

if TYPE_CHECKING:
    from simulation.model import CnzAgentBasedModel

from simulation.constants import (
    GB_PROPERTY_VALUE_WEIBULL_ALPHA,
    GB_PROPERTY_VALUE_WEIBULL_BETA,
    GB_RENOVATION_BUDGET_WEIBULL_ALPHA,
    GB_RENOVATION_BUDGET_WEIBULL_BETA,
    HAZARD_RATE_HEATING_SYSTEM_ALPHA,
    HAZARD_RATE_HEATING_SYSTEM_BETA,
    HEATING_SYSTEM_FUEL,
    BuiltForm,
    ConstructionYearBand,
    Element,
    Epc,
    EventTrigger,
    HeatingFuel,
    HeatingSystem,
    InsulationSegment,
    OccupantType,
    PropertyType,
)
from simulation.costs import (
    CAVITY_WALL_INSULATION_COST,
    DOUBLE_GLAZING_UPVC_COST,
    INTERNAL_WALL_INSULATION_COST,
    LOFT_INSULATION_JOISTS_COST,
)

HEAT_PUMPS = {HeatingSystem.HEAT_PUMP_AIR_SOURCE, HeatingSystem.HEAT_PUMP_GROUND_SOURCE}


def sample_interval_uniformly(interval: pd.Interval) -> float:
    return random.randint(interval.left, interval.right)


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
        heating_system_install_date: datetime.datetime,
        epc: Epc,
        potential_epc: Epc,
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
        self.heating_system_install_date = heating_system_install_date
        self.epc = epc
        self.potential_epc = potential_epc
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
    def true_with_probability(p: float) -> bool:
        return random.random() < p

    @staticmethod
    def weibull_hazard_rate(alpha: float, beta: float, age_years: float):
        # Source: # https://en.wikipedia.org/wiki/Weibull_distribution

        """
        alpha: A value > 1 indicates that failure rates increases over time (e.g. an ageing process)
        beta: The larger this value, the more 'spread out' the distribution is
        age_years: The age of an item subject to failures over time (e.g. heating_type, or vehicle)
        """

        return (alpha / beta) * (age_years / beta) ** (alpha - 1)

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

    @property
    def insulation_segment(self) -> InsulationSegment:
        # As per the property segmentation used in BEIS - WHAT DOES IT COST TO RETROFIT HOMES?

        if self.property_type == PropertyType.FLAT:
            if self.floor_area_sqm < 54:
                return InsulationSegment.SMALL_FLAT
            return InsulationSegment.LARGE_FLAT

        if (
            self.property_type == PropertyType.HOUSE
            and self.built_form == BuiltForm.MID_TERRACE
        ):
            return (
                InsulationSegment.SMALL_MID_TERRACE_HOUSE
                if self.floor_area_sqm < 76
                else InsulationSegment.LARGE_MID_TERRACE_HOUSE
            )

        if self.property_type == PropertyType.HOUSE and self.built_form in [
            BuiltForm.END_TERRACE,
            BuiltForm.SEMI_DETACHED,
        ]:
            return (
                InsulationSegment.SMALL_SEMI_END_TERRACE_HOUSE
                if self.floor_area_sqm < 80
                else InsulationSegment.LARGE_SEMI_END_TERRACE_HOUSE
            )

        if (
            self.property_type == PropertyType.HOUSE
            and self.built_form == BuiltForm.DETACHED
        ):
            return (
                InsulationSegment.SMALL_DETACHED_HOUSE
                if self.floor_area_sqm < 117
                else InsulationSegment.LARGE_DETACHED_HOUSE
            )

        if self.property_type == PropertyType.BUNGALOW:
            return InsulationSegment.BUNGALOW

    @property
    def is_heat_pump_suitable(self) -> bool:

        return (
            False
            if not all(
                [
                    self.is_heat_pump_suitable_archetype,
                    self.potential_epc.value <= Epc.C.value,
                ]
            )
            else True
        )

    def heating_system_age_years(self, current_datetime: datetime.datetime) -> float:
        return (current_datetime - self.heating_system_install_date).days / 365

    def evaluate_renovation(self, model) -> None:

        step_interval_years = model.step_interval / datetime.timedelta(days=365)
        proba_renovate = model.annual_renovation_rate * step_interval_years

        self.is_renovating = self.true_with_probability(proba_renovate)

    def decide_renovation_scope(self) -> None:

        # Derived from the VERD Project, 2012-2013. UK Data Service. SN: 7773, http://doi.org/10.5255/UKDA-SN-7773-1
        # Based upon the choices of houses in 'Stage 3' - finalising or actively renovating
        PROBA_HEATING_SYSTEM_UPDATE = 0.18
        PROBA_INSULATION_UPDATE = 0.33

        self.renovate_heating_system = self.true_with_probability(
            PROBA_HEATING_SYSTEM_UPDATE
        )
        self.renovate_insulation = self.true_with_probability(PROBA_INSULATION_UPDATE)

    def get_upgradable_insulation_elements(self) -> Set[Element]:

        measures_and_grades = zip(
            [Element.WALLS, Element.ROOF, Element.GLAZING],
            [
                self.walls_energy_efficiency,
                self.roof_energy_efficiency,
                self.windows_energy_efficiency,
            ],
        )

        MAX_ENERGY_EFFICIENCY_SCORE = 5
        return {
            measure
            for measure, grade in measures_and_grades
            if grade < MAX_ENERGY_EFFICIENCY_SCORE
        }

    def get_quote_insulation_elements(
        self, elements: Set[Element]
    ) -> Dict[Element, float]:

        insulation_quotes = {element: 0 for element in elements}
        for element in elements:
            if element == Element.WALLS:
                if self.is_solid_wall:
                    cost_range = INTERNAL_WALL_INSULATION_COST[self.insulation_segment]
                    insulation_quotes[element] = sample_interval_uniformly(cost_range)
                else:
                    cost_range = CAVITY_WALL_INSULATION_COST[self.insulation_segment]
                    insulation_quotes[element] = sample_interval_uniformly(cost_range)
            if element == Element.GLAZING:
                cost_range = DOUBLE_GLAZING_UPVC_COST[self.insulation_segment]
                insulation_quotes[element] = sample_interval_uniformly(cost_range)
            if element == Element.ROOF:
                cost_range = LOFT_INSULATION_JOISTS_COST[self.insulation_segment]
                insulation_quotes[element] = sample_interval_uniformly(cost_range)

        return insulation_quotes

    def choose_n_elements_to_insulate(self) -> int:

        # Derived from the VERD Project, 2012-2013. UK Data Service. SN: 7773, http://doi.org/10.5255/UKDA-SN-7773-1
        # Based upon the choices of houses in 'Stage 3' - finalising or actively renovating

        return random.choices([1, 2, 3], weights=[0.76, 0.17, 0.07])[0]

    def choose_insulation_elements(
        self, insulation_quotes: Dict[Element, float], num_elements: int
    ) -> Dict[Element, float]:

        return {
            element: insulation_quotes[element]
            for element in sorted(insulation_quotes, key=insulation_quotes.get)[
                :num_elements
            ]
        }

    def install_insulation_elements(
        self, insulation_elements: Dict[Element, float]
    ) -> None:

        for element in insulation_elements:
            if element == Element.ROOF:
                self.roof_energy_efficiency = 5
            if element == Element.WALLS:
                self.walls_energy_efficiency = 5
            if element == Element.GLAZING:
                self.windows_energy_efficiency = 5

        n_measures = len(insulation_elements)
        improved_epc_level = max(0, self.epc.value - n_measures)
        self.epc = Epc(improved_epc_level)

    def get_heating_system_options(
        self, model: "CnzAgentBasedModel", event_trigger: EventTrigger
    ) -> Set[HeatingSystem]:

        heating_system_options = model.heating_systems
        if not self.is_heat_pump_suitable or not self.is_heat_pump_aware:
            heating_system_options -= HEAT_PUMPS

        if self.off_gas_grid:
            heating_system_options -= {HeatingSystem.BOILER_GAS}
        else:
            heating_system_options -= {HeatingSystem.BOILER_OIL}

        if event_trigger == EventTrigger.BREAKDOWN:
            # if household already has a heat pump, they can reinstall that type of heat pump in a breakdown
            # heat pumps are otherwise unfeasible in a breakdown due to installation lead times
            unfeasible_heating_systems = HEAT_PUMPS - {self.heating_system}
            heating_system_options -= unfeasible_heating_systems

        return heating_system_options

    def update_heating_status(self, model: "CnzAgentBasedModel") -> None:

        step_interval_years = model.step_interval / datetime.timedelta(days=365)
        probability_density = self.weibull_hazard_rate(
            HAZARD_RATE_HEATING_SYSTEM_ALPHA,
            HAZARD_RATE_HEATING_SYSTEM_BETA,
            self.heating_system_age_years(model.current_datetime),
        )
        proba_failure = probability_density * step_interval_years
        if random.random() < proba_failure:
            self.heating_functioning = False

    def step(self, model):
        self.update_heating_status(model)
        if not self.heating_functioning:
            self.get_heating_system_options(model, event_trigger=EventTrigger.BREAKDOWN)

        self.evaluate_renovation(model)
        if self.is_renovating:
            self.decide_renovation_scope()
            if self.renovate_insulation:
                upgradable_elements = self.get_upgradable_insulation_elements()
                insulation_quotes = self.get_quote_insulation_elements(
                    upgradable_elements
                )
                chosen_elements = self.choose_insulation_elements(
                    insulation_quotes, self.choose_n_elements_to_insulate()
                )
                self.install_insulation_elements(chosen_elements)
            if self.renovate_heating_system:
                self.get_heating_system_options(
                    model, event_trigger=EventTrigger.RENOVATION
                )
