import datetime

import pandas as pd
import pytest
from dateutil.relativedelta import relativedelta

from simulation.constants import (
    ENGLAND_WALES_HOUSEHOLD_COUNT_2020,
    HEATING_SYSTEM_LIFETIME_YEARS,
    HOUSEHOLDS_PER_HEAT_PUMP_INSTALLER_FLOOR,
    BuiltForm,
    ConstructionYearBand,
    EPCRating,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import create_household_agents
from simulation.tests.common import household_factory, model_factory


class TestDomesticHeatingABM:
    def test_increment_timestep_increments_current_datetime(self) -> None:
        start_datetime = datetime.datetime.now()
        step_interval = datetime.timedelta(minutes=1440)
        model = model_factory(
            start_datetime=start_datetime, step_interval=step_interval
        )
        assert model.current_datetime == start_datetime

        model.increment_timestep()
        assert model.current_datetime == start_datetime + step_interval

    def test_increment_timestep_updates_boiler_upgrade_scheme_cumulative_spend_gbp(
        self,
    ) -> None:

        model = model_factory()
        assert model.boiler_upgrade_scheme_cumulative_spend_gbp == 0

        household_using_boiler_upgrade_grant_ASHP = household_factory()
        household_using_boiler_upgrade_grant_ASHP.boiler_upgrade_grant_used = 7_500

        household_using_boiler_upgrade_grant_GSHP = household_factory()
        household_using_boiler_upgrade_grant_GSHP.boiler_upgrade_grant_used = 7_500

        model.add_agents(
            [
                household_using_boiler_upgrade_grant_ASHP,
                household_using_boiler_upgrade_grant_GSHP,
            ]
        )

        model.increment_timestep()
        assert model.boiler_upgrade_scheme_cumulative_spend_gbp == 15_000

        model.increment_timestep()
        assert model.boiler_upgrade_scheme_cumulative_spend_gbp == 30_000

    def test_air_source_heat_pump_discount_factor_is_zero_if_no_discount_schedule_passed(
        self,
    ):

        model = model_factory(air_source_heat_pump_price_discount_schedule=None)

        assert model.air_source_heat_pump_discount_factor == 0

    def test_air_source_heat_pump_discount_factor_changes_when_crosses_discount_schedule_date(
        self,
    ):

        model = model_factory(
            start_datetime=datetime.datetime(2024, 2, 1),
            air_source_heat_pump_price_discount_schedule=[
                (datetime.datetime(2024, 2, 1), 0.1),
                (datetime.datetime(2024, 2, 2), 0.3),
            ],
            step_interval=datetime.timedelta(minutes=1440),
        )

        assert model.air_source_heat_pump_discount_factor == 0.1

        model.increment_timestep()
        assert model.air_source_heat_pump_discount_factor == 0.3

        model.increment_timestep()
        assert model.air_source_heat_pump_discount_factor == 0.3

    def test_heat_pump_installers_increases_over_time_with_positive_annual_growth_rate(
        self,
    ):

        model = model_factory(
            step_interval=relativedelta(months=60),
            heat_pump_installer_annual_growth_rate=0.5,
        )
        model.add_agents([household_factory() for _ in range(10_000)])
        heat_pump_installers = model.heat_pump_installers

        model.increment_timestep()
        future_heat_pump_installers = model.heat_pump_installers

        assert heat_pump_installers < future_heat_pump_installers

    def test_heat_pump_installer_count_increases_faster_with_higher_annual_growth_rate(
        self,
    ):

        model = model_factory(
            step_interval=relativedelta(months=120),
            heat_pump_installer_annual_growth_rate=0.1,
        )
        model.add_agents([household_factory() for _ in range(10_000)])
        model.increment_timestep()

        model_with_higher_installer_growth = model_factory(
            step_interval=relativedelta(months=120),
            heat_pump_installer_annual_growth_rate=0.6,
        )
        model_with_higher_installer_growth.add_agents(
            [household_factory() for _ in range(10_000)]
        )
        model_with_higher_installer_growth.increment_timestep()

        assert (
            model.heat_pump_installers
            < model_with_higher_installer_growth.heat_pump_installers
        )

    def test_heat_pump_installer_count_is_capped_by_ratio_of_installers_to_households(
        self,
    ):

        model = model_factory(
            step_interval=relativedelta(months=120),
            heat_pump_installer_annual_growth_rate=9,
        )
        model.add_agents([household_factory() for _ in range(10_000)])
        model.increment_timestep()

        hp_installer_maximum = int(
            model.household_count / HOUSEHOLDS_PER_HEAT_PUMP_INSTALLER_FLOOR
        )
        assert model.heat_pump_installers == hp_installer_maximum

    def test_heat_pump_installation_capacity_per_step_increases_with_step_interval(
        self,
    ):

        model_with_one_month_timestep = model_factory(
            step_interval=relativedelta(months=1),
        )

        model_with_six_month_timestep = model_factory(
            step_interval=relativedelta(months=6),
        )

        assert (
            model_with_one_month_timestep.heat_pump_installation_capacity_per_step
            < model_with_six_month_timestep.heat_pump_installation_capacity_per_step
        )

    def test_model_does_not_have_heat_pump_installation_capacity_if_installations_per_step_reached_step_capacity(
        self,
    ):
        model = model_factory()
        model.heat_pump_installations_at_current_step = (
            model.heat_pump_installation_capacity_per_step * 1.1
        )
        assert not model.has_heat_pump_installation_capacity

    def test_model_new_builds_per_step_is_zero_if_no_year_in_annual_new_builds(self):
        model = model_factory(annual_new_builds=None)
        assert model.new_builds_per_step == 0

        model = model_factory(
            start_datetime=datetime.datetime(2021, 1, 1),
            annual_new_builds={2022: 100},
        )
        assert model.new_builds_per_step == 0

    def test_model_new_builds_per_step_is_scaled_by_population_size(self):
        england_wales_new_builds = 120_000
        number_of_agents = 10_000
        model = model_factory(
            start_datetime=datetime.datetime(2021, 1, 1),
            step_interval=relativedelta(months=1),  # 1 step = 1 month
            annual_new_builds={2021: england_wales_new_builds},
        )
        model.add_agents([household_factory() for _ in range(number_of_agents)])
        population_scale_factor = number_of_agents / ENGLAND_WALES_HOUSEHOLD_COUNT_2020
        expected_new_builds_per_step = int(
            (england_wales_new_builds / 12) * population_scale_factor
        )
        assert model.new_builds_per_step == expected_new_builds_per_step

    @pytest.mark.parametrize("year", {2020, 2021, 2022, 2023, 2024})
    def test_model_does_not_install_heat_pumps_in_new_builds_before_2025(self, year):
        model = model_factory(
            start_datetime=datetime.datetime(year, 1, 1),
            annual_new_builds={year: 100},
        )
        assert model.heat_pump_installation_capacity_per_step_new_builds == 0

    def test_model_installs_heat_pumps_in_new_builds_post_2025(self):
        model = model_factory(
            start_datetime=datetime.datetime(2025, 1, 1),
            annual_new_builds={2025: 120_000},
        )
        model.add_agents([household_factory() for _ in range(10_000)])
        assert model.heat_pump_installation_capacity_per_step_new_builds > 0
        assert (
            model.heat_pump_installation_capacity_per_step_new_builds
            == model.new_builds_per_step
        )

    def test_model_does_not_install_heat_pumps_in_existing_builds_when_too_many_new_builds(
        self,
    ):
        model = model_factory(
            start_datetime=datetime.datetime(2025, 1, 1),
            annual_new_builds={2025: 120_000_000},
        )
        model.add_agents([household_factory() for _ in range(10_000)])
        assert model.heat_pump_installation_capacity_per_step_new_builds > 0
        assert model.heat_pump_installation_capacity_per_step_existing_builds == 0
        assert not model.has_heat_pump_installation_capacity

    def test_model_installs_heat_pumps_in_existing_builds_when_there_is_capacity(self):
        model = model_factory(
            start_datetime=datetime.datetime(2025, 1, 1),
            heat_pump_installer_count=1_000_000,
            annual_new_builds={2025: 120_000},
        )
        # We calculate the heat pump installers scaled to the number of agents in the model, so make sure there are sufficient agents
        model.add_agents([household_factory() for _ in range(10_000)])

        capacity_new_build, capacity_existing_build, capacity_total = (
            model.heat_pump_installation_capacity_per_step_new_builds,
            model.heat_pump_installation_capacity_per_step_existing_builds,
            model.heat_pump_installation_capacity_per_step,
        )
        assert capacity_new_build + capacity_existing_build == capacity_total
        assert 0 < capacity_new_build < capacity_existing_build
        assert model.has_heat_pump_installation_capacity


class TestCreateHouseholdAgents:

    household_population = pd.DataFrame(
        {
            "id": [1, 2],
            "location": ["Birmingham", "London"],
            "property_value_gbp": [264_000, 500_000],
            "total_floor_area_m2": [82, 120],
            "is_off_gas_grid": [False, False],
            "construction_year_band": ["BUILT_2007_ONWARDS", "BUILT_2007_ONWARDS"],
            "property_type": ["house", "house"],
            "built_form": ["mid_terrace", "detached"],
            "heating_system": ["boiler_gas", "boiler_gas"],
            "epc_rating": ["C", "D"],
            "potential_epc_rating": ["B", "B"],
            "occupant_type": ["owner_occupied", "owner_occupied"],
            "is_solid_wall": [False, False],
            "walls_energy_efficiency": [3, 3],
            "windows_energy_efficiency": [3, 3],
            "roof_energy_efficiency": [3, 3],
            "is_heat_pump_suitable_archetype": [True, False],
        }
    )

    simulation_start_datetime = datetime.datetime.now()
    all_agents_heat_pump_suitable = False

    def test_create_household_agents(self) -> None:
        heat_pump_awareness = 0.4
        heat_pump_awareness_due_to_campaign = 0.8

        household_agents = create_household_agents(
            self.household_population,
            self.simulation_start_datetime,
            self.all_agents_heat_pump_suitable,
            heat_pump_awareness,
            heat_pump_awareness_due_to_campaign,
        )
        household = next(household_agents)

        assert household.id == 1
        assert household.location == "Birmingham"
        assert household.property_value_gbp == 264_000
        assert household.total_floor_area_m2 == 82
        assert not household.is_off_gas_grid
        assert (
            household.construction_year_band == ConstructionYearBand.BUILT_2007_ONWARDS
        )
        assert household.property_type == PropertyType.HOUSE
        assert household.built_form == BuiltForm.MID_TERRACE
        assert household.heating_system == HeatingSystem.BOILER_GAS
        assert (
            self.simulation_start_datetime.date()
            - datetime.timedelta(days=365 * HEATING_SYSTEM_LIFETIME_YEARS)
            <= household.heating_system_install_date
            <= self.simulation_start_datetime.date()
        )
        assert household.epc_rating == EPCRating.C
        assert household.potential_epc_rating == EPCRating.B
        assert household.occupant_type == OccupantType.OWNER_OCCUPIED
        assert not household.is_solid_wall
        assert household.walls_energy_efficiency == 3
        assert household.windows_energy_efficiency == 3
        assert household.roof_energy_efficiency == 3
        assert household.is_heat_pump_suitable_archetype
        assert household.is_heat_pump_aware is not None
        assert household.is_heat_pump_aware_after_campaign is not None

        household = next(household_agents)

        with pytest.raises(StopIteration):
            next(household_agents)

    def test_all_household_agents_are_heat_pump_aware_with_maximum_awareness(
        self,
    ) -> None:
        heat_pump_awareness = 1.0
        heat_pump_awareness_due_to_campaign = 1.0

        household_agents = create_household_agents(
            self.household_population,
            self.simulation_start_datetime,
            self.all_agents_heat_pump_suitable,
            heat_pump_awareness,
            heat_pump_awareness_due_to_campaign,
        )

        for household in household_agents:
            assert household.is_heat_pump_aware
            assert household.is_heat_pump_aware_after_campaign

    def test_all_household_agents_become_heat_pump_aware_with_100_per_cent_campaign_success(
        self,
    ) -> None:
        heat_pump_awareness = 0.5
        heat_pump_awareness_due_to_campaign = 1.0

        household_agents = create_household_agents(
            self.household_population,
            self.simulation_start_datetime,
            self.all_agents_heat_pump_suitable,
            heat_pump_awareness,
            heat_pump_awareness_due_to_campaign,
        )

        for household in household_agents:
            assert household.is_heat_pump_aware_after_campaign

    def test_household_agents_do_not_change_awareness_with_no_increase_in_awareness_due_to_campaign(
        self,
    ) -> None:
        heat_pump_awareness = 0.5
        heat_pump_awareness_due_to_campaign = 0.5

        household_agents = create_household_agents(
            self.household_population,
            self.simulation_start_datetime,
            self.all_agents_heat_pump_suitable,
            heat_pump_awareness,
            heat_pump_awareness_due_to_campaign,
        )

        for household in household_agents:
            assert (
                household.is_heat_pump_aware
                == household.is_heat_pump_aware_after_campaign
            )

    def test_household_agents_awareness_cannot_decrease_due_to_campaign(self) -> None:
        # Even if `heat_pump_awareness_due_to_campaign` is less than `heat_pump_awareness`, the awareness cannot decrease
        heat_pump_awareness = 0.5
        heat_pump_awareness_due_to_campaign = 0.0

        household_agents = create_household_agents(
            self.household_population,
            self.simulation_start_datetime,
            self.all_agents_heat_pump_suitable,
            heat_pump_awareness,
            heat_pump_awareness_due_to_campaign,
        )

        for household in household_agents:
            assert (
                household.is_heat_pump_aware
                == household.is_heat_pump_aware_after_campaign
            )
