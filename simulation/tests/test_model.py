import datetime

import pandas as pd
import pytest
from dateutil.relativedelta import relativedelta

from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
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
        household_using_boiler_upgrade_grant_ASHP.boiler_upgrade_grant_used = 5_000

        household_using_boiler_upgrade_grant_GSHP = household_factory()
        household_using_boiler_upgrade_grant_GSHP.boiler_upgrade_grant_used = 6_000

        model.add_agents(
            [
                household_using_boiler_upgrade_grant_ASHP,
                household_using_boiler_upgrade_grant_GSHP,
            ]
        )

        model.increment_timestep()
        assert model.boiler_upgrade_scheme_cumulative_spend_gbp == 11_000

        model.increment_timestep()
        assert model.boiler_upgrade_scheme_cumulative_spend_gbp == 22_000

    def test_air_source_heat_pump_discount_factor_is_zero_if_no_discount_schedule_passed(
        self,
    ):

        model = model_factory(air_source_heat_pump_price_discount_schedule=None)

        assert model.air_source_heat_pump_discount_factor == 0

    def test_air_source_heat_pump_discount_factor_changes_when_crosses_discount_schedule_date(
        self,
    ):

        model = model_factory(
            start_datetime=datetime.datetime(2022, 2, 1),
            air_source_heat_pump_price_discount_schedule=[
                (datetime.datetime(2022, 2, 1), 0.1),
                (datetime.datetime(2022, 2, 2), 0.3),
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


def test_create_household_agents() -> None:
    household_population = pd.DataFrame(
        {
            "id": [1],
            "location": ["Birmingham"],
            "property_value_gbp": [264_000],
            "total_floor_area_m2": [82],
            "is_off_gas_grid": [False],
            "construction_year_band": ["BUILT_2007_ONWARDS"],
            "property_type": ["house"],
            "built_form": ["mid_terrace"],
            "heating_system": ["boiler_gas"],
            "epc_rating": ["C"],
            "potential_epc_rating": ["B"],
            "occupant_type": ["owner_occupied"],
            "is_solid_wall": [False],
            "walls_energy_efficiency": [3],
            "windows_energy_efficiency": [3],
            "roof_energy_efficiency": [3],
            "is_heat_pump_suitable_archetype": [True],
        }
    )
    heat_pump_awareness = 0.4
    simulation_start_datetime = datetime.datetime.now()
    all_agents_heat_pump_suitable = False
    household_agents = create_household_agents(
        household_population,
        heat_pump_awareness,
        simulation_start_datetime,
        all_agents_heat_pump_suitable,
    )
    household = next(household_agents)

    assert household.id == 1
    assert household.location == "Birmingham"
    assert household.property_value_gbp == 264_000
    assert household.total_floor_area_m2 == 82
    assert not household.is_off_gas_grid
    assert household.construction_year_band == ConstructionYearBand.BUILT_2007_ONWARDS
    assert household.property_type == PropertyType.HOUSE
    assert household.built_form == BuiltForm.MID_TERRACE
    assert household.heating_system == HeatingSystem.BOILER_GAS
    assert (
        simulation_start_datetime.date()
        - datetime.timedelta(days=365 * HEATING_SYSTEM_LIFETIME_YEARS)
        <= household.heating_system_install_date
        <= simulation_start_datetime.date()
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

    with pytest.raises(StopIteration):
        next(household_agents)
