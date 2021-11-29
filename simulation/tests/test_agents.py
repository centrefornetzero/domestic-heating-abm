import pandas as pd

from simulation.agents import Household
from simulation.constants import (
    HEATING_SYSTEM_LIFETIME_YEARS,
    BuiltForm,
    Epc,
    HeatingFuel,
    HeatingSystem,
    OccupantType,
    PropertyType,
    ConstructionYearBand,
)


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
        assert household.is_heat_pump_aware is not None
