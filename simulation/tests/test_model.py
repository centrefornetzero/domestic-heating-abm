import datetime

import pandas as pd
import pytest

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

    def test_air_source_heat_pump_price_discount_schedule_created_when_no_schedule_passed(
        self,
    ) -> None:

        model = model_factory(air_source_heat_pump_price_discount_schedule=[])

        assert model.air_source_heat_pump_price_discount_schedule == {
            model.start_datetime: 0,
            model.end_datetime: 0,
        }

    def test_air_source_heat_pump_price_discount_schedule_generated_for_full_simulation_when_partial_discount_schedule_passed(
        self,
    ) -> None:

        model = model_factory(
            start_datetime=datetime.datetime(2022, 1, 1),
            end_datetime=datetime.datetime(2035, 1, 1),
            air_source_heat_pump_price_discount_schedule=[
                (datetime.datetime(2023, 1, 1), 0.1),
                (datetime.datetime(2026, 1, 1), 0.2),
            ],
        )

        assert model.air_source_heat_pump_price_discount_schedule == {
            datetime.datetime(2022, 1, 1): 0,
            datetime.datetime(2023, 1, 1): 0.1,
            datetime.datetime(2026, 1, 1): 0.2,
            datetime.datetime(2035, 1, 1): 0.2,
        }

    def test_air_source_heat_pump_discount_factor_is_zero_if_no_discount_schedule_passed(
        self,
    ):

        model = model_factory(air_source_heat_pump_price_discount_schedule=[])

        assert model.air_source_heat_pump_discount_factor == 0

    def test_air_source_heat_pump_discount_factor_increases_if_passed_discount_schedule_of_increasing_factors(
        self,
    ):
        model = model_factory(
            start_datetime=datetime.datetime(2022, 2, 1),
            air_source_heat_pump_price_discount_schedule=[
                (datetime.datetime(2022, 2, 1), 0),
                (datetime.datetime(2022, 4, 1), 0.3),
            ],
        )

        first_discount_factor = model.air_source_heat_pump_discount_factor

        model.increment_timestep()
        second_discount_factor = model.air_source_heat_pump_discount_factor

        assert second_discount_factor > first_discount_factor


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
