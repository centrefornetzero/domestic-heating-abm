import random

import pytest

from simulation.constants import BOILERS, HEAT_PUMPS, HeatingSystem
from simulation.costs import (
    get_heating_fuel_costs_net_present_value,
    get_unit_and_install_costs,
)
from simulation.tests.common import household_factory


class TestCosts:
    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_cost_of_any_heating_system_is_cheaper_if_already_installed(
        self, heating_system
    ) -> None:
        household_sticking_same_system = household_factory(
            heating_system=heating_system
        )

        alternative_system = random.choice(list(set(HeatingSystem) - {heating_system}))
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

    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_fuel_bills_net_present_value_decreases_as_discount_rate_increases(
        self,
        heating_system,
    ) -> None:

        num_look_ahead_years = random.randint(2, 10)
        household = household_factory(
            property_value_gbp=random.randint(50_000, 300_000)
        )
        wealthier_household = household_factory(
            property_value_gbp=household.property_value_gbp * 1.1
        )

        assert household.discount_rate > wealthier_household.discount_rate

        assert get_heating_fuel_costs_net_present_value(
            household, heating_system, num_look_ahead_years
        ) < get_heating_fuel_costs_net_present_value(
            wealthier_household, heating_system, num_look_ahead_years
        )

    @pytest.mark.parametrize("heat_pump", set(HEAT_PUMPS))
    def test_heat_pumps_are_cheaper_to_reinstall_than_install_first_time(
        self,
        heat_pump,
    ) -> None:

        household = household_factory(heating_system=HeatingSystem.BOILER_GAS)
        new_heat_pump_quote = get_unit_and_install_costs(household, heat_pump)

        household.heating_system = heat_pump
        reinstall_heat_pump_quote = get_unit_and_install_costs(household, heat_pump)

        assert reinstall_heat_pump_quote < new_heat_pump_quote
