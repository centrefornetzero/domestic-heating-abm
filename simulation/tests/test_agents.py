import datetime
import random

import numpy as np
import pytest

from simulation.agents import Household
from simulation.constants import (
    MAX_HEAT_PUMP_CAPACITY_KW,
    MIN_HEAT_PUMP_CAPACITY_KW,
    BuiltForm,
    ConstructionYearBand,
    Element,
    Epc,
    EventTrigger,
    HeatingFuel,
    HeatingSystem,
    OccupantType,
    PropertyType,
)
from simulation.model import CnzAgentBasedModel


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
    }
    return CnzAgentBasedModel(**{**default_values, **model_attributes})


HEAT_PUMPS = {HeatingSystem.HEAT_PUMP_AIR_SOURCE, HeatingSystem.HEAT_PUMP_GROUND_SOURCE}


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
            heating_system_install_date=datetime.date(1995, 1, 1),
            epc=Epc.C,
            potential_epc=Epc.B,
            occupant_type=OccupantType.RENTER_PRIVATE,
            is_solid_wall=False,
            walls_energy_efficiency=4,
            windows_energy_efficiency=4,
            roof_energy_efficiency=2,
            is_heat_pump_suitable_archetype=True,
            is_heat_pump_aware=True,
        )
        assert household.location == "London"
        assert household.property_value == 400_000
        assert household.floor_area_sqm == 100
        assert not household.off_gas_grid
        assert household.construction_year_band == ConstructionYearBand.BUILT_1919_1944
        assert household.property_type == PropertyType.HOUSE
        assert household.built_form == BuiltForm.MID_TERRACE
        assert household.heating_system == HeatingSystem.BOILER_ELECTRIC
        assert household.heating_system_install_date == datetime.date(1995, 1, 1)
        assert household.epc == Epc.C
        assert household.potential_epc == Epc.B
        assert household.occupant_type == OccupantType.RENTER_PRIVATE
        assert not household.is_solid_wall
        assert household.walls_energy_efficiency == 4
        assert household.windows_energy_efficiency == 4
        assert household.roof_energy_efficiency == 2
        assert household.is_heat_pump_suitable_archetype
        assert household.heating_fuel == HeatingFuel.ELECTRICITY
        assert household.is_heat_pump_aware
        assert household.is_renovating is not None

    def test_household_renovation_budget_increases_with_property_value(self) -> None:
        low_property_value_household = household_factory(property_value=100_000)
        medium_property_value_household = household_factory(property_value=300_000)
        high_property_value_household = household_factory(property_value=500_000)

        assert (
            low_property_value_household.renovation_budget
            < medium_property_value_household.renovation_budget
            < high_property_value_household.renovation_budget
        )

    def test_renovation_budget_greater_than_or_equal_to_zero_and_less_than_total_property_value(
        self,
    ) -> None:
        household = household_factory(property_value=random.randint(0, 5_000_000))

        assert household.renovation_budget >= 0
        assert household.renovation_budget < household.property_value

    def test_household_is_renovating_state_updates(
        self,
    ) -> None:

        model = CnzAgentBasedModel(
            start_datetime=datetime.datetime.now(),
            step_interval=datetime.timedelta(days=365),
            annual_renovation_rate=1.0,
        )

        household = household_factory()
        assert not household.is_renovating
        household.evaluate_renovation(model)
        assert household.is_renovating

    def test_household_flat_without_roof_cannot_upgrade_roof_insulation(
        self,
    ) -> None:

        household = household_factory(roof_energy_efficiency=np.NaN)
        assert Element.ROOF not in household.get_upgradable_insulation_elements()

    def test_household_elements_under_max_energy_efficiency_score_are_upgradable(
        self,
    ) -> None:

        household = household_factory(
            roof_energy_efficiency=5,
            windows_energy_efficiency=3,
            walls_energy_efficiency=2,
        )

        assert household.get_upgradable_insulation_elements() == set(
            [Element.GLAZING, Element.WALLS]
        )

    def test_household_gets_non_zero_insulation_quotes_for_all_upgradable_elements(
        self,
    ) -> None:

        household = household_factory(
            roof_energy_efficiency=random.randint(1, 5),
            windows_energy_efficiency=random.randint(1, 5),
            walls_energy_efficiency=random.randint(1, 5),
        )

        upgradable_elements = household.get_upgradable_insulation_elements()
        insulation_quotes = household.get_quote_insulation_elements(upgradable_elements)

        assert set(insulation_quotes.keys()) == upgradable_elements
        assert all(quote > 0 for quote in insulation_quotes.values())

    def test_household_chooses_one_to_three_insulation_measures_to_install(
        self,
    ) -> None:

        household = household_factory()
        assert 0 < household.choose_n_elements_to_insulate() <= 3

    def test_household_chooses_cheapest_insulation_measures(
        self,
    ) -> None:

        household = household_factory()
        insulation_quotes = {
            Element.WALLS: 5_000,
            Element.GLAZING: 4_000,
            Element.ROOF: 1_000,
        }
        chosen_measures = household.choose_insulation_elements(insulation_quotes, 2)

        assert chosen_measures.keys() == set([Element.ROOF, Element.GLAZING])

        chosen_measures = household.choose_insulation_elements(insulation_quotes, 1)

        assert chosen_measures.keys() == {Element.ROOF}

    def test_installation_of_insulation_measures_improves_element_energy_efficiency_and_epc(
        self,
    ) -> None:

        household = household_factory(
            roof_energy_efficiency=3, walls_energy_efficiency=2, epc=Epc.D
        )
        household.install_insulation_elements({Element.ROOF: 1_000})

        assert household.roof_energy_efficiency == 5
        assert household.epc == Epc.C

        household.install_insulation_elements({Element.WALLS: 3_000})

        assert household.walls_energy_efficiency == 5
        assert household.epc == Epc.B

    def test_impact_of_installing_insulation_measures_is_capped_at_epc_A(
        self,
    ) -> None:

        epc_A_household = household_factory(
            roof_energy_efficiency=4,
            walls_energy_efficiency=5,
            windows_energy_efficiency=5,
            epc=Epc.A,
        )
        epc_A_household.install_insulation_elements({Element.ROOF: 1_000})

        assert epc_A_household.roof_energy_efficiency == 5
        assert epc_A_household.epc == Epc.A

    def test_households_with_potential_epc_below_C_are_not_heat_pump_suitable(
        self,
    ) -> None:

        low_potential_epc_household = household_factory(potential_epc=Epc.D)

        assert not low_potential_epc_household.is_heat_pump_suitable

    def test_households_not_suitable_archetype_are_not_heat_pump_suitable(
        self,
    ) -> None:

        unsuitable_archetype_household = household_factory(
            is_heat_pump_suitable_archetype=False
        )

        assert not unsuitable_archetype_household.is_heat_pump_suitable

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_heat_pumps_not_in_heating_system_options_if_household_not_heat_pump_suitable(
        self,
        event_trigger,
    ) -> None:

        unsuitable_household = household_factory(potential_epc=Epc.D)
        model = model_factory()
        assert not HEAT_PUMPS.intersection(
            unsuitable_household.get_heating_system_options(
                model, event_trigger=event_trigger
            )
        )

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_heat_pumps_not_in_heating_system_options_if_household_not_heat_pump_aware(
        self,
        event_trigger,
    ) -> None:

        unaware_household = household_factory(is_heat_pump_aware=False)
        model = model_factory()
        heating_system_options = unaware_household.get_heating_system_options(
            model, event_trigger
        )
        assert heating_system_options.intersection(HEAT_PUMPS) == set()

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_gas_boiler_not_in_heating_system_options_if_household_off_gas_grid(
        self, event_trigger
    ) -> None:

        off_gas_grid_household = household_factory(off_gas_grid=True)
        model = model_factory()
        heating_system_options = off_gas_grid_household.get_heating_system_options(
            model, event_trigger
        )
        assert heating_system_options.intersection({HeatingSystem.BOILER_GAS}) == set()

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_oil_boiler_not_in_heating_system_options_if_household_off_gas_grid(
        self,
        event_trigger,
    ) -> None:

        on_gas_grid_household = household_factory(off_gas_grid=False)
        model = model_factory()
        heating_system_options = on_gas_grid_household.get_heating_system_options(
            model, event_trigger
        )
        assert heating_system_options.intersection({HeatingSystem.BOILER_OIL}) == set()

    def test_heat_pump_not_in_heating_system_options_at_breakdown_event(
        self,
    ) -> None:

        heat_pump_suitable_household = household_factory(
            epc=Epc.B,
            is_heat_pump_suitable_archetype=True,
            heating_system=HeatingSystem.BOILER_GAS,
        )
        model = model_factory()
        heating_system_options = (
            heat_pump_suitable_household.get_heating_system_options(
                model, EventTrigger.BREAKDOWN
            )
        )
        assert heating_system_options.intersection(HEAT_PUMPS) == set()

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_current_heat_pump_type_in_heating_system_options_at_breakdown_event_if_household_has_heat_pump(
        self,
        heat_pump,
    ) -> None:

        household_with_heat_pump = household_factory(
            epc=Epc.B, is_heat_pump_suitable_archetype=True, heating_system=heat_pump
        )
        model = model_factory()
        assert household_with_heat_pump.is_heat_pump_suitable
        heating_system_options = household_with_heat_pump.get_heating_system_options(
            model, EventTrigger.BREAKDOWN
        )
        assert heating_system_options.intersection(HEAT_PUMPS) == {heat_pump}

    def test_household_with_ancient_heating_system_experiences_failure(self) -> None:

        household = household_factory(
            heating_system_install_date=datetime.date(1960, 1, 1)
        )
        model = model_factory(start_datetime=datetime.datetime.now())

        assert household.heating_functioning

        household.update_heating_status(model)

        assert not household.heating_functioning

    def test_household_with_lower_wealth_has_higher_discount_rate(self) -> None:

        household = household_factory(property_value=random.randint(50_000, 400_000))
        higher_wealth_household = household_factory(
            property_value=household.property_value * 1.1
        )

        assert household.discount_rate > higher_wealth_household.discount_rate

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_larger_household_has_equal_or_higher_required_heat_pump_kw_capacity(
        self, heat_pump
    ) -> None:

        household = household_factory(floor_area_sqm=random.randint(20, 180))
        larger_household = household_factory(
            floor_area_sqm=household.floor_area_sqm * 1.1
        )

        assert household.compute_heat_pump_capacity_kw(
            heat_pump
        ) <= larger_household.compute_heat_pump_capacity_kw(heat_pump)

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_household_required_heat_pump_kw_capacity_within_allowed_range(
        self, heat_pump
    ) -> None:

        household = household_factory(floor_area_sqm=random.randint(20, 180))

        assert (
            MIN_HEAT_PUMP_CAPACITY_KW[heat_pump]
            <= household.compute_heat_pump_capacity_kw(heat_pump)
            <= MAX_HEAT_PUMP_CAPACITY_KW[heat_pump]
        )
