import datetime

import pandas as pd
import pytest

from simulation.constants import (
    BuiltForm,
    Epc,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import CnzAgentBasedModel, create_households


class TestCnzAgentBasedModel:
    def test_step_increments_current_datetime(self) -> None:
        start_datetime = datetime.datetime.now()
        step_interval = datetime.timedelta(minutes=1440)
        model = CnzAgentBasedModel(start_datetime, step_interval)
        assert model.current_datetime == start_datetime

        model.step()
        assert model.current_datetime == start_datetime + step_interval


def test_create_households_yields_correctly_initialised_household() -> None:
    household_distribution = pd.DataFrame(
        {
            "location": ["Birmingham"],
            "property_value": [264_000],
            "floor_area_sqm": [82],
            "off_gas_grid": [False],
            "construction_year_band": ["1945-1964"],
            "property_type": ["house"],
            "built_form": ["mid_terrace"],
            "heating_system": ["boiler_gas"],
            "epc": ["C"],
            "occupant_type": ["owner_occupier"],
            "is_solid_wall": [False],
            "walls_energy_efficiency": [3],
            "windows_energy_efficiency": [3],
            "roof_energy_efficiency": [3],
            "is_heat_pump_suitable_archetype": [True],
        }
    )
    num_households = 1
    households = create_households(num_households, household_distribution)
    household = next(households)

    assert household.location == "Birmingham"
    assert household.property_value == 264_000
    assert household.floor_area_sqm == 82
    assert not household.off_gas_grid
    assert 1945 <= household.construction_year <= 1964
    assert household.property_type == PropertyType.HOUSE
    assert household.built_form == BuiltForm.MID_TERRACE
    assert household.heating_system == HeatingSystem.BOILER_GAS
    assert household.epc == Epc.C
    assert household.occupant_type == OccupantType.OWNER_OCCUPIER
    assert not household.is_solid_wall
    assert household.walls_energy_efficiency == 3
    assert household.windows_energy_efficiency == 3
    assert household.roof_energy_efficiency == 3
    assert household.is_heat_pump_suitable_archetype

    with pytest.raises(StopIteration):
        next(households)


def test_create_many_households() -> None:
    household_distribution = pd.DataFrame(
        {
            "location": ["Birmingham"],
            "property_value": [264_000],
            "floor_area_sqm": [82],
            "off_gas_grid": [False],
            "construction_year_band": ["1945-1964"],
            "property_type": ["house"],
            "built_form": ["mid_terrace"],
            "heating_system": ["boiler_gas"],
            "epc": ["C"],
            "occupant_type": ["owner_occupier"],
            "is_solid_wall": [False],
            "walls_energy_efficiency": [3],
            "windows_energy_efficiency": [3],
            "roof_energy_efficiency": [3],
            "is_heat_pump_suitable_archetype": [True],
        }
    )
    num_households = 100
    households = create_households(num_households, household_distribution)
    assert len(list(households)) == num_households
