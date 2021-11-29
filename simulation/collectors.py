import datetime
from typing import TYPE_CHECKING, Any, Callable, List

from abm import collect_when
from simulation.agents import Household

if TYPE_CHECKING:
    from simulation.model import CnzAgentBasedModel


def household_id(household) -> int:
    return id(household)


def household_heating_system(household) -> str:
    return household.heating_system.name


def model_current_datetime(model) -> datetime.datetime:
    return model.current_datetime


def is_first_step(model: "CnzAgentBasedModel") -> bool:
    return model.current_datetime == model.start_datetime + model.step_interval


def get_agent_collectors(
    model: "CnzAgentBasedModel",
) -> List[Callable[[Household], Any]]:
    return [
        collect_when(model, is_first_step)(household_id),
        household_heating_system,
    ]


model_collectors = [
    model_current_datetime,
]
