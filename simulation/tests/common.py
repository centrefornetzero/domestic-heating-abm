import datetime

from simulation.agents import Household
from simulation.constants import (
    BuiltForm,
    ConstructionYearBand,
    Epc,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import CnzAgentBasedModel


def household_factory(**agent_attributes):
    default_values = {
        "location": "Test Location",
        "property_value_gbp": 264_000,
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
        "household_num_lookahead_years": 3,
        "heating_system_hassle_factor": 0.7,
    }
    return CnzAgentBasedModel(**{**default_values, **model_attributes})
