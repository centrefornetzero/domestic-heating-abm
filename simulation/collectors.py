import datetime
from typing import TYPE_CHECKING, Any, Callable, List

from abm import collect_when
from simulation.agents import Household
from simulation.constants import Element, HeatingSystem

if TYPE_CHECKING:
    from simulation.model import DomesticHeatingABM


def household_id(household) -> int:
    return household.id


def household_location(household) -> str:
    return household.location


def household_property_value_gbp(household) -> int:
    return household.property_value_gbp


def household_floor_area_sqm(household) -> int:
    return household.total_floor_area_m2


def household_is_off_gas_grid(household) -> bool:
    return household.is_off_gas_grid


def household_construction_year_band(household) -> str:
    return household.construction_year_band.name


def household_property_type(household) -> str:
    return household.property_type.name


def household_built_form(household) -> str:
    return household.built_form.name


def household_heating_system(household) -> str:
    return household.heating_system.name


def household_heating_functioning(household) -> bool:
    return household.heating_functioning


def household_heating_install_date(household) -> datetime.date:
    return household.heating_system_install_date


def household_epc(household) -> str:
    return household.epc_rating.name


def household_potential_epc(household) -> str:
    return household.potential_epc_rating.name


def household_occupant_type(household) -> str:
    return household.occupant_type.name


def household_is_solid_wall(household) -> bool:
    return household.is_solid_wall


def household_walls_energy_efficiency(household) -> int:
    return household.walls_energy_efficiency


def household_windows_energy_efficiency(household) -> int:
    return household.windows_energy_efficiency


def household_roof_energy_efficiency(household) -> int:
    return household.roof_energy_efficiency


def household_is_heat_pump_suitable_archetype(household) -> bool:
    return household.is_heat_pump_suitable_archetype


def household_is_heat_pump_aware(household) -> bool:
    return household.is_heat_pump_aware


def household_is_renovating(household) -> bool:
    return household.is_renovating


def household_is_renovating_insulation(household) -> bool:
    return household.renovate_insulation


def household_is_renovating_heating_system(household) -> bool:
    return household.renovate_heating_system


def household_wealth_percentile(household) -> float:
    return household.wealth_percentile


def household_discount_rate(household) -> float:
    return household.discount_rate


def household_renovation_budget(household) -> int:
    return int(household.renovation_budget)


def household_is_heat_pump_suitable(household) -> bool:
    return household.is_heat_pump_suitable


def household_annual_kwh_heating_demand(household) -> int:
    return int(household.annual_kwh_heating_demand)


def household_annual_heating_fuel_bill(household) -> int:
    return household.annual_heating_fuel_bill


def household_epc_c_upgrade_cost_roof(household) -> int:
    return int(household.epc_c_upgrade_costs.get(Element.ROOF) or 0)


def household_epc_c_upgrade_cost_walls(household) -> int:
    return int(household.epc_c_upgrade_costs.get(Element.WALLS) or 0)


def household_epc_c_upgrade_cost_windows(household) -> int:
    return int(household.epc_c_upgrade_costs.get(Element.GLAZING) or 0)


def household_heating_system_total_cost_boiler_gas(household) -> int:
    return int(household.heating_system_total_costs.get(HeatingSystem.BOILER_GAS) or 0)


def household_heating_system_total_cost_boiler_oil(household) -> int:
    return int(household.heating_system_total_costs.get(HeatingSystem.BOILER_OIL) or 0)


def household_heating_system_total_cost_boiler_electric(household) -> int:
    return int(
        household.heating_system_total_costs.get(HeatingSystem.BOILER_ELECTRIC) or 0
    )


def household_heating_system_total_cost_heat_pump_air_source(household) -> int:
    return int(
        household.heating_system_total_costs.get(HeatingSystem.HEAT_PUMP_AIR_SOURCE)
        or 0
    )


def household_heating_system_total_cost_heat_pump_ground_source(household) -> int:
    return int(
        household.heating_system_total_costs.get(HeatingSystem.HEAT_PUMP_GROUND_SOURCE)
        or 0
    )


def model_current_datetime(model) -> datetime.datetime:
    return model.current_datetime


def is_first_timestep(model: "DomesticHeatingABM") -> bool:
    return model.current_datetime == model.start_datetime + model.step_interval


def get_agent_collectors(
    model: "DomesticHeatingABM",
) -> List[Callable[[Household], Any]]:
    return [
        household_id,
        collect_when(model, is_first_timestep)(household_location),
        collect_when(model, is_first_timestep)(household_property_value_gbp),
        collect_when(model, is_first_timestep)(household_floor_area_sqm),
        collect_when(model, is_first_timestep)(household_is_off_gas_grid),
        collect_when(model, is_first_timestep)(household_construction_year_band),
        collect_when(model, is_first_timestep)(household_property_type),
        collect_when(model, is_first_timestep)(household_built_form),
        collect_when(model, is_first_timestep)(household_potential_epc),
        collect_when(model, is_first_timestep)(household_occupant_type),
        collect_when(model, is_first_timestep)(household_is_solid_wall),
        collect_when(model, is_first_timestep)(
            household_is_heat_pump_suitable_archetype
        ),
        collect_when(model, is_first_timestep)(household_wealth_percentile),
        collect_when(model, is_first_timestep)(household_discount_rate),
        collect_when(model, is_first_timestep)(household_renovation_budget),
        collect_when(model, is_first_timestep)(household_is_heat_pump_suitable),
        collect_when(model, is_first_timestep)(household_is_heat_pump_aware),
        household_heating_system,
        household_heating_functioning,
        household_heating_install_date,
        household_epc,
        household_walls_energy_efficiency,
        household_windows_energy_efficiency,
        household_roof_energy_efficiency,
        household_is_renovating,
        household_is_renovating_insulation,
        household_is_renovating_heating_system,
        household_annual_kwh_heating_demand,
        household_annual_heating_fuel_bill,
        household_epc_c_upgrade_cost_roof,
        household_epc_c_upgrade_cost_walls,
        household_epc_c_upgrade_cost_windows,
        household_heating_system_total_cost_boiler_gas,
        household_heating_system_total_cost_boiler_oil,
        household_heating_system_total_cost_boiler_electric,
        household_heating_system_total_cost_heat_pump_air_source,
        household_heating_system_total_cost_heat_pump_ground_source,
    ]


model_collectors = [
    model_current_datetime,
]
