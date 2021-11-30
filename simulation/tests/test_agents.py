import datetime
import random

import numpy as np

from simulation.agents import Household
from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    ConstructionYearBand,
    Element,
    Epc,
    HeatingFuel,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import CnzAgentBasedModel


def household_factory(**agent_attributes):
    default_values = {
        "location": "Test Location",
        "property_value": 264_000,
        "floor_area_sqm": 82,
        "off_gas_grid": False,
        "construction_year_band": ConstructionYearBand.BUILT_1919_1944,
        "property_type": PropertyType.HOUSE,
        "built_form": BuiltForm.MID_TERRACE,
        "heating_system": HeatingSystem.BOILER_GAS,
        "epc": Epc.D,
        "occupant_type": OccupantType.OWNER_OCCUPIER,
        "is_solid_wall": False,
        "walls_energy_efficiency": 3,
        "windows_energy_efficiency": 3,
        "roof_energy_efficiency": 3,
        "is_heat_pump_suitable_archetype": True,
        "is_heat_pump_aware": True,
    }
    return Household(**{**default_values, **agent_attributes})


class TestHousehold:
    def test_create_household(self) -> None:
        household = household_factory(
            location="London",
            property_value=400_000,
            floor_area_sqm=100,
            off_gas_grid=False,
            construction_year_band=ConstructionYearBand.BUILT_1919_1944,
            property_type=PropertyType.HOUSE,
            built_form=BuiltForm.MID_TERRACE,
            heating_system=HeatingSystem.BOILER_ELECTRIC,
            epc=Epc.C,
            occupant_type=OccupantType.RENTER_PRIVATE,
            is_solid_wall=False,
            walls_energy_efficiency=4,
            windows_energy_efficiency=4,
            roof_energy_efficiency=2,
            is_heat_pump_suitable_archetype=True,
            is_heat_pump_aware=True,
        )
        assert household.location == "London"
        assert household.property_value == 400_000
        assert household.floor_area_sqm == 100
        assert not household.off_gas_grid
        assert household.construction_year_band == ConstructionYearBand.BUILT_1919_1944
        assert household.property_type == PropertyType.HOUSE
        assert household.built_form == BuiltForm.MID_TERRACE
        assert household.heating_system == HeatingSystem.BOILER_ELECTRIC
        assert 0 <= household.heating_system_age <= HEATING_SYSTEM_LIFETIME_YEARS
        assert household.epc == Epc.C
        assert household.occupant_type == OccupantType.RENTER_PRIVATE
        assert not household.is_solid_wall
        assert household.walls_energy_efficiency == 4
        assert household.windows_energy_efficiency == 4
        assert household.roof_energy_efficiency == 2
        assert household.is_heat_pump_suitable_archetype
        assert household.heating_fuel == HeatingFuel.ELECTRICITY
        assert household.is_heat_pump_aware
        assert household.is_renovating is not None

    def test_household_renovation_budget_increases_with_property_value(self) -> None:
        low_property_value_household = household_factory(property_value=100_000)
        medium_property_value_household = household_factory(property_value=300_000)
        high_property_value_household = household_factory(property_value=500_000)

        assert (
            low_property_value_household.renovation_budget
            < medium_property_value_household.renovation_budget
            < high_property_value_household.renovation_budget
        )

    def test_renovation_budget_greater_than_or_equal_to_zero_and_less_than_total_property_value(
        self,
    ) -> None:
        household = household_factory(property_value=random.randint(0, 5_000_000))

        assert household.renovation_budget >= 0
        assert household.renovation_budget < household.property_value

    def test_household_is_renovating_state_updates(
        self,
    ) -> None:

        model = CnzAgentBasedModel(
            start_datetime=datetime.datetime.now(),
            step_interval=datetime.timedelta(days=365),
            annual_renovation_rate=1.0,
        )

        household = household_factory()
        assert not household.is_renovating
        household.evaluate_renovation(model)
        assert household.is_renovating

    def test_household_flat_without_roof_cannot_upgrade_roof_insulation(
        self,
    ) -> None:

        household = household_factory(roof_energy_efficiency=np.NaN)
        assert Element.ROOF not in household.get_upgradable_insulation_elements()

    def test_household_upgradable_elements_reflect_energy_efficiency_scores(
        self,
    ) -> None:

        household = household_factory(
            roof_energy_efficiency=5,
            windows_energy_efficiency=3,
            walls_energy_efficiency=2,
        )

        assert household.get_upgradable_insulation_elements() == set(
            [Element.GLAZING, Element.WALLS]
        )
