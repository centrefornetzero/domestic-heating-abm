import datetime

from dateutil.relativedelta import relativedelta

from simulation.agents import Household
from simulation.constants import (
    BuiltForm,
    ConstructionYearBand,
    EPCRating,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import DomesticHeatingABM


def household_factory(**agent_attributes):
    default_values = {
        "id": 1,
        "location": "Test Location",
        "property_value_gbp": 264_000,
        "total_floor_area_m2": 82,
        "is_off_gas_grid": False,
        "construction_year_band": ConstructionYearBand.BUILT_2007_ONWARDS,
        "property_type": PropertyType.HOUSE,
        "built_form": BuiltForm.MID_TERRACE,
        "heating_system": HeatingSystem.BOILER_GAS,
        "heating_system_install_date": datetime.date(2021, 1, 1),
        "epc_rating": EPCRating.D,
        "potential_epc_rating": EPCRating.C,
        "occupant_type": OccupantType.OWNER_OCCUPIED,
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
        "step_interval": relativedelta(months=1),
        "annual_renovation_rate": 0.05,
        "household_num_lookahead_years": 3,
        "heating_system_hassle_factor": 0.7,
        "rented_heating_system_hassle_factor": 0.7,
        "interventions": [],
        "gas_oil_boiler_ban_datetime": datetime.datetime(2035, 1, 1),
        "gas_oil_boiler_ban_announce_datetime": datetime.datetime(2025, 1, 1),
        "price_gbp_per_kwh_gas": 0.062,
        "price_gbp_per_kwh_electricity": 0.245,
        "price_gbp_per_kwh_oil": 0.068,
        "air_source_heat_pump_price_discount_schedule": None,
        "heat_pump_installer_count": 2_800,
        "heat_pump_installer_annual_growth_rate": 0,
        "annual_new_builds": None,
        "heat_pump_awareness": 0.5,
        "campaign_target_heat_pump_awareness": 0.8,
        "heat_pump_awareness_campaign_date": datetime.datetime(2028, 1, 1),
        "population_heat_pump_awareness": [],
    }

    return DomesticHeatingABM(**{**default_values, **model_attributes})
