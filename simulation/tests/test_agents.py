import datetime
import random

import numpy as np
import pytest

from simulation.constants import (
    BOILERS,
    HEAT_PUMPS,
    MAX_HEAT_PUMP_CAPACITY_KW,
    MIN_HEAT_PUMP_CAPACITY_KW,
    BuiltForm,
    ConstructionYearBand,
    Element,
    EPCRating,
    EventTrigger,
    HeatingFuel,
    HeatingSystem,
    InterventionType,
    OccupantType,
    PropertySize,
    PropertyType,
)
from simulation.tests.common import household_factory, model_factory


class TestHousehold:
    def test_create_household_factory(self) -> None:
        household = household_factory(
            id=1,
            location="London",
            property_value_gbp=400_000,
            total_floor_area_m2=100,
            is_off_gas_grid=False,
            construction_year_band=ConstructionYearBand.BUILT_1900_1929,
            property_type=PropertyType.HOUSE,
            built_form=BuiltForm.MID_TERRACE,
            heating_system=HeatingSystem.BOILER_ELECTRIC,
            heating_system_install_date=datetime.date(1995, 1, 1),
            epc_rating=EPCRating.C,
            potential_epc_rating=EPCRating.B,
            occupant_type=OccupantType.RENTED_PRIVATE,
            is_solid_wall=False,
            walls_energy_efficiency=4,
            windows_energy_efficiency=4,
            roof_energy_efficiency=2,
            is_heat_pump_suitable_archetype=True,
            is_heat_pump_aware=True,
        )
        assert household.id == 1
        assert household.location == "London"
        assert household.property_value_gbp == 400_000
        assert household.total_floor_area_m2 == 100
        assert not household.is_off_gas_grid
        assert household.construction_year_band == ConstructionYearBand.BUILT_1900_1929
        assert household.property_type == PropertyType.HOUSE
        assert household.built_form == BuiltForm.MID_TERRACE
        assert household.heating_system == HeatingSystem.BOILER_ELECTRIC
        assert household.heating_system_install_date == datetime.date(1995, 1, 1)
        assert household.epc_rating == EPCRating.C
        assert household.potential_epc_rating == EPCRating.B
        assert household.occupant_type == OccupantType.RENTED_PRIVATE
        assert not household.is_solid_wall
        assert household.walls_energy_efficiency == 4
        assert household.windows_energy_efficiency == 4
        assert household.roof_energy_efficiency == 2
        assert household.is_heat_pump_suitable_archetype
        assert household.heating_fuel == HeatingFuel.ELECTRICITY
        assert household.is_heat_pump_aware
        assert household.is_renovating is not None

    def test_household_renovation_budget_increases_with_property_value(self) -> None:
        low_property_value_household = household_factory(property_value_gbp=100_000)
        medium_property_value_household = household_factory(property_value_gbp=300_000)
        high_property_value_household = household_factory(property_value_gbp=500_000)

        assert (
            low_property_value_household.renovation_budget
            < medium_property_value_household.renovation_budget
            < high_property_value_household.renovation_budget
        )

    def test_renovation_budget_greater_than_or_equal_to_zero_and_less_than_total_property_value(
        self,
    ) -> None:
        household = household_factory(property_value_gbp=random.randint(0, 5_000_000))

        assert household.renovation_budget >= 0
        assert household.renovation_budget < household.property_value_gbp

    def test_household_is_renovating_state_updates(
        self,
    ) -> None:

        model = model_factory(
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

    def test_household_chooses_one_to_three_insulation_measures_to_install_at_renovation(
        self,
    ) -> None:

        household = household_factory()
        assert (
            0
            < household.get_num_insulation_elements(
                event_trigger=EventTrigger.RENOVATION
            )
            <= 3
        )

    @pytest.mark.parametrize("epc_rating", list(EPCRating))
    def test_num_insulation_measures_chosen_by_household_corresponds_to_current_epc_value(
        self,
        epc_rating,
    ) -> None:

        household = household_factory(epc_rating=epc_rating)
        if household.epc_rating.value < EPCRating.C.value:
            expected_insulation_elements = EPCRating.C.value - epc_rating.value
            assert (
                household.get_num_insulation_elements(
                    event_trigger=EventTrigger.EPC_C_UPGRADE
                )
                == expected_insulation_elements
            )
        if household.epc_rating.value >= EPCRating.C.value:
            assert (
                household.get_num_insulation_elements(
                    event_trigger=EventTrigger.EPC_C_UPGRADE
                )
                == 0
            )

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
            roof_energy_efficiency=3, walls_energy_efficiency=2, epc_rating=EPCRating.D
        )
        household.install_insulation_elements({Element.ROOF: 1_000})

        assert household.roof_energy_efficiency == 5
        assert household.epc_rating == EPCRating.C

        household.install_insulation_elements({Element.WALLS: 3_000})

        assert household.walls_energy_efficiency == 5
        assert household.epc_rating == EPCRating.B

    def test_impact_of_installing_insulation_measures_is_capped_at_epc_A(
        self,
    ) -> None:

        epc_A_household = household_factory(
            roof_energy_efficiency=4,
            walls_energy_efficiency=5,
            windows_energy_efficiency=5,
            epc_rating=EPCRating.A,
        )
        epc_A_household.install_insulation_elements({Element.ROOF: 1_000})

        assert epc_A_household.roof_energy_efficiency == 5
        assert epc_A_household.epc_rating == EPCRating.A

    def test_households_with_potential_epc_below_C_are_not_heat_pump_suitable(
        self,
    ) -> None:

        low_potential_epc_household = household_factory(
            potential_epc_rating=EPCRating.D
        )

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

        unsuitable_household = household_factory(potential_epc_rating=EPCRating.D)
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
    def test_gas_boiler_not_in_heating_system_options_if_household_is_off_gas_grid(
        self, event_trigger
    ) -> None:

        is_off_gas_grid_household = household_factory(is_off_gas_grid=True)
        model = model_factory()
        heating_system_options = is_off_gas_grid_household.get_heating_system_options(
            model, event_trigger
        )
        assert heating_system_options.intersection({HeatingSystem.BOILER_GAS}) == set()

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_oil_boiler_not_in_heating_system_options_if_household_is_off_gas_grid(
        self,
        event_trigger,
    ) -> None:

        on_gas_grid_household = household_factory(is_off_gas_grid=False)
        model = model_factory()
        heating_system_options = on_gas_grid_household.get_heating_system_options(
            model, event_trigger
        )
        assert heating_system_options.intersection({HeatingSystem.BOILER_OIL}) == set()

    @pytest.mark.parametrize("event_trigger", list(EventTrigger))
    def test_electric_boilers_not_in_heating_system_options_if_household_is_not_small(
        self,
        event_trigger,
    ) -> None:

        larger_household = household_factory(
            total_floor_area_m2=random.randint(67, 200)
        )
        model = model_factory()

        assert larger_household.property_size != PropertySize.SMALL

        heating_system_options = larger_household.get_heating_system_options(
            model, event_trigger
        )

        assert (
            heating_system_options.intersection({HeatingSystem.BOILER_ELECTRIC})
            == set()
        )

    def test_heat_pump_not_in_heating_system_options_at_breakdown_event(
        self,
    ) -> None:

        heat_pump_suitable_household = household_factory(
            epc_rating=EPCRating.B,
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
            epc_rating=EPCRating.B,
            is_heat_pump_suitable_archetype=True,
            heating_system=heat_pump,
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

        household = household_factory(
            property_value_gbp=random.randint(50_000, 400_000)
        )
        higher_wealth_household = household_factory(
            property_value_gbp=household.property_value_gbp * 1.1
        )

        assert household.discount_rate > higher_wealth_household.discount_rate

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_larger_household_has_equal_or_higher_required_heat_pump_kw_capacity(
        self, heat_pump
    ) -> None:

        household = household_factory(total_floor_area_m2=random.randint(20, 180))
        larger_household = household_factory(
            total_floor_area_m2=household.total_floor_area_m2 * 1.1
        )

        assert household.compute_heat_pump_capacity_kw(
            heat_pump
        ) <= larger_household.compute_heat_pump_capacity_kw(heat_pump)

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_household_required_heat_pump_kw_capacity_within_allowed_range(
        self, heat_pump
    ) -> None:

        household = household_factory(total_floor_area_m2=random.randint(20, 180))

        assert (
            MIN_HEAT_PUMP_CAPACITY_KW[heat_pump]
            <= household.compute_heat_pump_capacity_kw(heat_pump)
            <= MAX_HEAT_PUMP_CAPACITY_KW[heat_pump]
        )

    @pytest.mark.parametrize("heating_system", set(HeatingSystem))
    def test_annual_heating_demand_increases_with_floor_area(
        self,
        heating_system,
    ) -> None:

        household = household_factory(
            total_floor_area_m2=random.randint(20, 180), heating_system=heating_system
        )
        larger_household = household_factory(
            total_floor_area_m2=household.total_floor_area_m2 * 1.1,
            heating_system=heating_system,
        )

        assert (
            household.annual_kwh_heating_demand
            < larger_household.annual_kwh_heating_demand
        )

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_annual_heating_demand_is_lower_for_more_efficient_heating_systems(
        self,
        heat_pump,
    ) -> None:

        household_with_gas_boiler = household_factory(
            total_floor_area_m2=random.randint(20, 180),
            heating_system=HeatingSystem.BOILER_GAS,
        )
        household_with_heat_pump = household_factory(
            total_floor_area_m2=household_with_gas_boiler.total_floor_area_m2,
            heating_system=heat_pump,
        )

        assert (
            household_with_heat_pump.annual_kwh_heating_demand
            < household_with_gas_boiler.annual_kwh_heating_demand
        )

    @pytest.mark.parametrize("epc_rating", list(EPCRating))
    def test_household_chooses_insulation_elements_at_epc_C_upgrade_event_if_current_epc_worse_than_C(
        self,
        epc_rating,
    ) -> None:

        household = household_factory(epc_rating=epc_rating)

        if epc_rating.value >= EPCRating.C.value:
            assert (
                household.get_chosen_insulation_costs(
                    event_trigger=EventTrigger.EPC_C_UPGRADE
                )
                == {}
            )

        if epc_rating.value < EPCRating.C.value:
            chosen_insulation_elements = household.get_chosen_insulation_costs(
                event_trigger=EventTrigger.EPC_C_UPGRADE
            )

            assert chosen_insulation_elements

    @pytest.mark.parametrize("heating_system", list(HeatingSystem))
    def test_heating_system_is_not_hassle_if_already_installed_or_a_boiler(
        self,
        heating_system,
    ) -> None:

        household = household_factory(heating_system=heating_system)
        if heating_system == household.heating_system:
            assert not household.is_heating_system_hassle(heating_system)
        if heating_system in BOILERS:
            assert not household.is_heating_system_hassle(heating_system)

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_heat_pumps_are_hassle_if_not_already_installed(
        self,
        heat_pump,
    ) -> None:

        household = household_factory(heating_system=random.choices(list(BOILERS))[0])
        assert household.is_heating_system_hassle(heat_pump)

    @pytest.mark.parametrize("heating_system", list(HeatingSystem))
    def test_heat_pumps_never_selected_if_hassle_factor_is_one_and_not_currently_installed(
        self,
        heating_system,
    ) -> None:

        household = household_factory(heating_system=HeatingSystem.BOILER_GAS)
        costs = {
            HeatingSystem.BOILER_GAS: 2_000,
            HeatingSystem.HEAT_PUMP_AIR_SOURCE: 2_000,
        }

        assert (
            household.choose_heating_system(costs, heating_system_hassle_factor=1)
            == HeatingSystem.BOILER_GAS
        )

    @pytest.mark.parametrize("heating_system", list(HeatingSystem))
    def test_households_installs_heating_systems_at_model_current_datetime_and_heating_becomes_functioning(
        self,
        heating_system,
    ) -> None:

        household = household_factory(
            heating_system=random.choices(list(HeatingSystem))[0]
        )
        household.heating_functioning = False
        model = model_factory()
        household.install_heating_system(heating_system, model)

        assert household.heating_system == heating_system
        assert household.heating_system_install_date == model.current_datetime.date()

        household.update_heating_status(model)

        assert household.heating_functioning

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_total_heating_system_costs_are_lower_for_heat_pumps_if_model_intervention_rhi(
        self, heat_pump
    ):

        household = household_factory(heating_system=random.choices(list(BOILERS))[0])

        model_without_rhi = model_factory()
        model_with_rhi = model_factory(interventions=[InterventionType.RHI])

        assert sum(
            household.get_total_heating_system_costs(heat_pump, model_with_rhi)
        ) < sum(household.get_total_heating_system_costs(heat_pump, model_without_rhi))

    @pytest.mark.parametrize("heating_system", list(HeatingSystem))
    def test_heating_fuel_costs_are_zero_for_landlords(self, heating_system):

        current_heating_system = random.choices(list(HeatingSystem))[0]

        private_rented_household = household_factory(
            occupant_type=OccupantType.RENTED_PRIVATE,
            heating_system=current_heating_system,
        )
        social_rented_household = household_factory(
            occupant_type=OccupantType.RENTED_SOCIAL,
            heating_system=current_heating_system,
        )
        owned_household = household_factory(
            occupant_type=OccupantType.OWNER_OCCUPIED,
            heating_system=current_heating_system,
        )
        model = model_factory()
        assert (
            private_rented_household.get_heating_fuel_costs(heating_system, model) == 0
        )
        assert (
            social_rented_household.get_heating_fuel_costs(heating_system, model) == 0
        )
        assert owned_household.get_heating_fuel_costs(heating_system, model) > 0

    @pytest.mark.parametrize("heat_pump", HEAT_PUMPS)
    def test_total_heating_system_costs_are_lower_for_heat_pumps_if_model_intervention_boiler_upgrade_scheme(
        self, heat_pump
    ):

        household = household_factory(heating_system=random.choices(list(BOILERS))[0])

        model_without_boiler_upgrade_scheme = model_factory(
            start_datetime=datetime.datetime(2023, 1, 1, 0, 0)
        )
        model_with_boiler_upgrade_scheme = model_factory(
            start_datetime=datetime.datetime(2023, 1, 1, 0, 0),
            interventions=[InterventionType.BOILER_UPGRADE_SCHEME],
        )

        assert sum(
            household.get_total_heating_system_costs(
                heat_pump, model_with_boiler_upgrade_scheme
            )
        ) < sum(
            household.get_total_heating_system_costs(
                heat_pump, model_without_boiler_upgrade_scheme
            )
        )

    @pytest.mark.parametrize("event_trigger", set(EventTrigger))
    def test_gas_and_oil_boilers_are_not_in_heating_options_if_gas_oil_ban_intervention_active(
        self, event_trigger
    ):

        household = household_factory(heating_system=random.choices(list(BOILERS))[0])

        model_with_gas_oil_boiler_ban = model_factory(
            start_datetime=datetime.datetime(2035, 3, 1),
            interventions=[InterventionType.GAS_OIL_BOILER_BAN],
            gas_oil_boiler_ban_datetime=datetime.datetime(2030, 1, 1),
        )

        banned_heating_systems = [HeatingSystem.BOILER_GAS, HeatingSystem.BOILER_OIL]
        heating_system_options = household.get_heating_system_options(
            model_with_gas_oil_boiler_ban, event_trigger=event_trigger
        )

        assert all(
            heating_system not in heating_system_options
            for heating_system in banned_heating_systems
        )

    @pytest.mark.parametrize("event_trigger", set(EventTrigger))
    def test_heat_pump_suitable_households_can_choose_heat_pumps_in_all_event_triggers_and_irrespective_of_awareness_if_gas_oil_ban_intervention_active(
        self, event_trigger
    ):

        household = household_factory(
            heating_system=random.choices(list(BOILERS))[0],
            is_heat_pump_aware=random.choices([True, False])[0],
            is_heat_pump_suitable_archetype=True,
        )

        model_with_gas_oil_boiler_ban = model_factory(
            start_datetime=datetime.datetime(2035, 3, 1),
            interventions=[InterventionType.GAS_OIL_BOILER_BAN],
            gas_oil_boiler_ban_datetime=datetime.datetime(2030, 1, 1),
        )

        heating_system_options = household.get_heating_system_options(
            model_with_gas_oil_boiler_ban, event_trigger=event_trigger
        )

        assert all(
            heating_system in heating_system_options for heating_system in HEAT_PUMPS
        )
