import datetime
import random

import pytest

from simulation.agents import Household
from simulation.constants import (
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.costs import get_unit_and_install_costs
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
        "heating_system_install_date": datetime.date(2021, 1, 1),
        "epc": Epc.D,
        "potential_epc": Epc.C,
        "occupant_type": OccupantType.OWNER_OCCUPIER,
        "is_solid_wall": False,
        "walls_energy_efficiency": 3,
        "windows_energy_efficiency": 3,
        "roof_energy_efficiency": 3,
        "is_heat_pump_suitable_archetype": True,
        "is_heat_pump_aware": True,
    }
    return Household(**{**default_values, **agent_attributes})


def model_factory(**model_attributes):
    default_values = {
        "start_datetime": datetime.datetime.now(),
        "step_interval": datetime.timedelta(minutes=1440),
        "annual_renovation_rate": 0.05,
    }
    return CnzAgentBasedModel(**{**default_values, **model_attributes})


HEAT_PUMPS = {HeatingSystem.HEAT_PUMP_AIR_SOURCE, HeatingSystem.HEAT_PUMP_GROUND_SOURCE}
BOILERS = {
    HeatingSystem.BOILER_GAS,
    HeatingSystem.BOILER_OIL,
    HeatingSystem.BOILER_ELECTRIC,
}


class TestCosts:
    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_cost_of_any_heating_system_is_cheaper_if_already_installed(
        self, heating_system
    ) -> None:
        household_sticking_same_system = household_factory(
            heating_system=heating_system
        )

        alternative_system = random.choice(
            [system for system in set(HeatingSystem) if system != heating_system]
        )
        household_switching_system = household_factory(
            heating_system=alternative_system
        )

        assert get_unit_and_install_costs(
            household_sticking_same_system, heating_system
        ) < get_unit_and_install_costs(household_switching_system, heating_system)

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_cost_of_heat_pump_increases_with_kw_capacity_required(
        self,
        heat_pump,
    ) -> None:

        household = household_factory(
            floor_area_sqm=random.randint(20, 200), heating_system=heat_pump
        )
        larger_household = household_factory(
            floor_area_sqm=household.floor_area_sqm * 1.2,
            heating_system=heat_pump,
        )

        assert household.compute_heat_pump_capacity_kw(
            heat_pump
        ) <= larger_household.compute_heat_pump_capacity_kw(heat_pump)
        assert get_unit_and_install_costs(
            household, heat_pump
        ) <= get_unit_and_install_costs(larger_household, heat_pump)

    @pytest.mark.parametrize("boiler", BOILERS)
    def test_cost_of_boiler_increases_with_property_size(
        self,
        boiler,
    ) -> None:
        household = household_factory(
            floor_area_sqm=random.randint(20, 200), heating_system=boiler
        )
        larger_household = household_factory(
            floor_area_sqm=household.floor_area_sqm * 1.5, heating_system=boiler
        )

        assert get_unit_and_install_costs(
            household, boiler
        ) <= get_unit_and_install_costs(larger_household, boiler)
