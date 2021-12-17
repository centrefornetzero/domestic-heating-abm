import datetime

import pandas as pd
import pytest

from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import create_households
from simulation.tests.common import model_factory


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


def test_create_households_yields_correctly_initialised_household() -> None:
    household_distribution = pd.DataFrame(
        {
            "location": ["Birmingham"],
            "property_value_gbp": [264_000],
            "floor_area_sqm": [82],
            "off_gas_grid": [False],
            "construction_year_band": ["BUILT_2007_ONWARDS"],
            "property_type": ["house"],
            "built_form": ["mid_terrace"],
            "heating_system": ["boiler_gas"],
            "epc": ["C"],
            "potential_epc": ["B"],
            "occupant_type": ["owner_occupier"],
            "is_solid_wall": [False],
            "walls_energy_efficiency": [3],
            "windows_energy_efficiency": [3],
            "roof_energy_efficiency": [3],
            "is_heat_pump_suitable_archetype": [True],
        }
    )
    num_households = 1
    heat_pump_awareness = 0.4
    simulation_start_datetime = datetime.datetime.now()
    households = create_households(
        num_households,
        household_distribution,
        heat_pump_awareness,
        simulation_start_datetime,
    )
    household = next(households)

    assert household.location == "Birmingham"
    assert household.property_value_gbp == 264_000
    assert household.floor_area_sqm == 82
    assert not household.off_gas_grid
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
    assert household.epc == Epc.C
    assert household.potential_epc == Epc.B
    assert household.occupant_type == OccupantType.OWNER_OCCUPIER
    assert not household.is_solid_wall
    assert household.walls_energy_efficiency == 3
    assert household.windows_energy_efficiency == 3
    assert household.roof_energy_efficiency == 3
    assert household.is_heat_pump_suitable_archetype
    assert household.is_heat_pump_aware is not None

    with pytest.raises(StopIteration):
        next(households)


def test_create_many_households() -> None:
    household_distribution = pd.DataFrame(
        {
            "location": ["Birmingham"],
            "property_value_gbp": [264_000],
            "floor_area_sqm": [82],
            "off_gas_grid": [False],
            "construction_year_band": ["BUILT_2007_ONWARDS"],
            "property_type": ["house"],
            "built_form": ["mid_terrace"],
            "heating_system": ["boiler_gas"],
            "epc": ["C"],
            "potential_epc": ["B"],
            "occupant_type": ["owner_occupier"],
            "is_solid_wall": [False],
            "walls_energy_efficiency": [3],
            "windows_energy_efficiency": [3],
            "roof_energy_efficiency": [3],
            "is_heat_pump_suitable_archetype": [True],
        }
    )
    num_households = 100
    heat_pump_awareness = 0.4
    simulation_start_datetime = datetime.datetime.now()
    households = create_households(
        num_households,
        household_distribution,
        heat_pump_awareness,
        simulation_start_datetime,
    )
    assert len(list(households)) == num_households
