import datetime
import random

import pytest

from simulation.constants import (
    BOILERS,
    ENGLAND_WALES_HOUSEHOLD_COUNT_2020,
    HEAT_PUMPS,
    HeatingSystem,
)
from simulation.costs import (
    estimate_boiler_upgrade_scheme_grant,
    estimate_rhi_annual_payment,
    get_heating_fuel_costs_net_present_value,
    get_unit_and_install_costs,
)
from simulation.tests.common import household_factory, model_factory


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

        model = model_factory()

        assert get_unit_and_install_costs(
            household_sticking_same_system, heating_system, model
        ) < get_unit_and_install_costs(
            household_switching_system, heating_system, model
        )

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_cost_of_heat_pump_increases_with_kw_capacity_required(
        self,
        heat_pump,
    ) -> None:

        household = household_factory(
            total_floor_area_m2=random.randint(20, 200), heating_system=heat_pump
        )
        larger_household = household_factory(
            total_floor_area_m2=household.total_floor_area_m2 * 1.2,
            heating_system=heat_pump,
        )

        model = model_factory()

        assert household.compute_heat_pump_capacity_kw(
            heat_pump
        ) <= larger_household.compute_heat_pump_capacity_kw(heat_pump)
        assert get_unit_and_install_costs(
            household, heat_pump, model
        ) <= get_unit_and_install_costs(larger_household, heat_pump, model)

    @pytest.mark.parametrize("boiler", BOILERS)
    def test_cost_of_boiler_increases_with_property_size(
        self,
        boiler,
    ) -> None:
        household = household_factory(
            total_floor_area_m2=random.randint(20, 200), heating_system=boiler
        )
        larger_household = household_factory(
            total_floor_area_m2=household.total_floor_area_m2 * 1.5,
            heating_system=boiler,
        )
        model = model_factory()
        assert get_unit_and_install_costs(
            household, boiler, model
        ) <= get_unit_and_install_costs(larger_household, boiler, model)

    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_fuel_bills_net_present_value_decreases_as_discount_rate_increases(
        self,
        heating_system,
    ) -> None:

        household = household_factory(
            property_value_gbp=random.randint(50_000, 300_000)
        )
        wealthier_household = household_factory(
            property_value_gbp=household.property_value_gbp * 1.1
        )

        num_look_ahead_years = random.randint(2, 10)
        model = model_factory(household_num_lookahead_years=num_look_ahead_years)

        assert household.discount_rate > wealthier_household.discount_rate

        assert get_heating_fuel_costs_net_present_value(
            household, heating_system, model
        ) < get_heating_fuel_costs_net_present_value(
            wealthier_household, heating_system, model
        )

    @pytest.mark.parametrize("heat_pump", set(HEAT_PUMPS))
    def test_heat_pumps_are_cheaper_to_reinstall_than_install_first_time(
        self,
        heat_pump,
    ) -> None:

        household = household_factory(heating_system=HeatingSystem.BOILER_GAS)
        model = model_factory()

        new_heat_pump_quote = get_unit_and_install_costs(household, heat_pump, model)

        household.heating_system = heat_pump
        reinstall_heat_pump_quote = get_unit_and_install_costs(
            household, heat_pump, model
        )

        assert reinstall_heat_pump_quote < new_heat_pump_quote

    @pytest.mark.parametrize("heat_pump", set(HEAT_PUMPS))
    def test_rhi_annual_payments_are_non_zero_for_households_switching_to_heat_pumps(
        self, heat_pump
    ):

        household_with_boiler = household_factory(
            heating_system=random.choices(list(BOILERS))[0]
        )

        assert estimate_rhi_annual_payment(household_with_boiler, heat_pump) > 0

    @pytest.mark.parametrize("boiler", set(BOILERS))
    def test_rhi_annual_payments_zero_for_households_switching_to_boilers(self, boiler):

        household = household_factory(
            heating_system=random.choices(list(HeatingSystem))[0]
        )

        assert estimate_rhi_annual_payment(household, boiler) == 0

    @pytest.mark.parametrize("heat_pump", set(HEAT_PUMPS))
    def test_rhi_annual_payments_reach_cap_for_large_households(self, heat_pump):

        mansion = household_factory(
            heating_system=random.choices(list(BOILERS))[0],
            total_floor_area_m2=random.randint(500, 1_000),
        )

        larger_mansion = household_factory(
            heating_system=mansion.heating_system,
            total_floor_area_m2=mansion.total_floor_area_m2 * 1.1,
        )

        assert estimate_rhi_annual_payment(
            mansion, heat_pump
        ) == estimate_rhi_annual_payment(larger_mansion, heat_pump)

    def test_air_source_heat_pumps_unit_install_costs_are_adjusted_by_discount_factor_across_discount_schedule(
        self,
    ):

        discount_factor = 0.3
        household = household_factory(heating_system=HeatingSystem.HEAT_PUMP_AIR_SOURCE)
        model = model_factory(
            start_datetime=datetime.datetime(2022, 1, 1),
            step_interval=datetime.timedelta(minutes=1440),
            air_source_heat_pump_price_discount_schedule=[
                (datetime.datetime(2022, 1, 2), discount_factor),
            ],
        )
        first_quote = get_unit_and_install_costs(
            household, HeatingSystem.HEAT_PUMP_AIR_SOURCE, model
        )

        model.increment_timestep()
        later_quote = get_unit_and_install_costs(
            household, HeatingSystem.HEAT_PUMP_AIR_SOURCE, model
        )

        assert later_quote == int((1 - discount_factor) * first_quote)

    @pytest.mark.parametrize("boiler", set(BOILERS))
    def test_boiler_upgrade_scheme_grant_is_zero_for_boilers_within_grant_window(
        self, boiler
    ):

        start_datetime = datetime.datetime(2022, 4, 1, 0, 0)
        end_datetime = datetime.datetime(2025, 4, 1, 0, 0)
        random_n_days = random.randrange((end_datetime - start_datetime).days)
        start_datetime = start_datetime + datetime.timedelta(days=random_n_days)

        model = model_factory(
            start_datetime=start_datetime,
        )

        assert estimate_boiler_upgrade_scheme_grant(boiler, model) == 0

    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_boiler_upgrade_scheme_grant_is_zero_when_outside_grant_window(
        self, heating_system
    ):

        model = model_factory(start_datetime=datetime.datetime(2026, 1, 1, 0, 0))
        model.add_agents([household_factory()])

        assert estimate_boiler_upgrade_scheme_grant(heating_system, model) == 0

    @pytest.mark.parametrize("heat_pump", set(HEAT_PUMPS))
    def test_boiler_upgrade_scheme_grant_is_zero_when_grant_cap_exceeded(
        self, heat_pump
    ):

        model = model_factory(
            start_datetime=datetime.datetime(2023, 1, 1, 0, 0),
        )

        num_households = random.randint(0, 5)
        model.add_agents([household_factory()] * num_households)

        model_population_scale = (
            ENGLAND_WALES_HOUSEHOLD_COUNT_2020 / model.household_count
        )
        boiler_upgrade_scheme_budget_scaled = 450_000_000 / model_population_scale

        model.boiler_upgrade_scheme_cumulative_spend_gbp = (
            boiler_upgrade_scheme_budget_scaled * 0.8
        )
        assert estimate_boiler_upgrade_scheme_grant(heat_pump, model) > 0

        model.boiler_upgrade_scheme_cumulative_spend_gbp = (
            boiler_upgrade_scheme_budget_scaled
        )
        assert estimate_boiler_upgrade_scheme_grant(heat_pump, model) == 0

    def test_boiler_upgrade_scheme_grant_is_non_zero_for_heat_pumps_when_grant_is_active(
        self,
    ):

        model = model_factory(
            start_datetime=datetime.datetime(2023, 1, 1, 0, 0),
        )
        model.add_agents([household_factory()])

        assert (
            estimate_boiler_upgrade_scheme_grant(
                HeatingSystem.HEAT_PUMP_AIR_SOURCE, model
            )
            == 5_000
        )
        assert (
            estimate_boiler_upgrade_scheme_grant(
                HeatingSystem.HEAT_PUMP_GROUND_SOURCE, model
            )
            == 6_000
        )
