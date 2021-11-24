import enum
from typing import Dict


class PropertyType(enum.Enum):
    HOUSE = 0
    FLAT = 1
    BUNGALOW = 2


class BuiltForm(enum.Enum):
    MID_TERRACE = 0
    SEMI_DETACHED = 1
    DETACHED = 2
    END_TERRACE = 3


class OccupantType(enum.Enum):
    OWNER_OCCUPIER = 0
    RENTER_PRIVATE = 1
    RENTER_SOCIAL = 1


class Epc(enum.Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6


class HeatingSystem(enum.Enum):
    BOILER_GAS = 0
    BOILER_OIL = 1
    BOILER_ELECTRIC = 2
    HEAT_PUMP_AIR_SOURCE = 3
    HEAT_PUMP_GROUND_SOURCE = 4


class HeatingFuel(enum.Enum):
    GAS = 0
    ELECTRICITY = 1
    OIL = 2


HEATING_SYSTEM_FUEL: Dict[HeatingSystem, HeatingFuel] = {
    HeatingSystem.BOILER_GAS: HeatingFuel.GAS,
    HeatingSystem.BOILER_OIL: HeatingFuel.OIL,
    HeatingSystem.BOILER_ELECTRIC: HeatingFuel.ELECTRICITY,
    HeatingSystem.HEAT_PUMP_AIR_SOURCE: HeatingFuel.ELECTRICITY,
    HeatingSystem.HEAT_PUMP_GROUND_SOURCE: HeatingFuel.ELECTRICITY,
}

HEATING_SYSTEM_LIFETIME_YEARS = 15
