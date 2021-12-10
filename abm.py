import functools
import json
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

import pandas as pd
from tqdm.auto import trange

T = TypeVar("T")
AgentCallable = Callable[["Agent"], Any]
ModelCallable = Callable[["AgentBasedModel"], Any]
History = Iterator[Tuple[List[Dict[str, Any]], Dict[str, Any]]]


class OrderedSpace:
    def __init__(self) -> None:
        self.agents: List["Agent"] = list()

    def add_agent(self, agent: "Agent") -> None:
        self.agents.append(agent)

    def __contains__(self, agent: "Agent") -> bool:
        return agent in self.agents

    def __iter__(self) -> Iterator["Agent"]:
        yield from self.agents


class Agent:
    def make_decisions(self, model: Optional["AgentBasedModel"] = None) -> None:
        raise NotImplementedError


class AgentBasedModel:
    def __init__(self, space: Optional[OrderedSpace] = None, **properties: Any) -> None:
        self.space = space if space else OrderedSpace()
        for attribute, value in properties.items():
            setattr(self, attribute, value)

    def add_agent(self, agent: Agent) -> None:
        self.space.add_agent(agent)

    def add_agents(self, agents: Iterable[Agent]) -> None:
        for agent in agents:
            self.add_agent(agent)

    def increment_timestep(self) -> None:
        raise NotImplementedError

    def run(
        self,
        time_steps: int,
        agent_callables: Optional[List[AgentCallable]] = None,
        model_callables: Optional[List[ModelCallable]] = None,
    ) -> History:
        if agent_callables is None:
            agent_callables = []

        if model_callables is None:
            model_callables = []

        for _ in trange(time_steps, desc="Running simulation"):
            try:
                self.increment_timestep()
            except NotImplementedError:
                pass

            agent_data = []

            for agent in self.space:
                agent.make_decisions(self)
                agent_datum = {
                    agent_callable.__name__: agent_callable(agent)
                    for agent_callable in agent_callables
                    if agent_callable(agent) is not None
                }
                agent_data.append(agent_datum)

            model_data = {
                model_callable.__name__: model_callable(self)
                for model_callable in model_callables
            }

            yield agent_data, model_data


def collect_when(
    model: AgentBasedModel, condition: Callable[[AgentBasedModel], bool]
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    def collect_when_decorator(
        callable: Callable[..., T]
    ) -> Callable[..., Optional[T]]:
        @functools.wraps(callable)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            if condition(model):
                return callable(*args, **kwargs)
            return None

        return wrapper

    return collect_when_decorator


def write_jsonlines(history: History, filename: str) -> None:
    with open(filename, "w") as file:
        for step in history:
            file.write(json.dumps(step, default=str) + "\n")


def read_jsonlines(filename: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    with open(filename, "r") as file:
        decoded_lines = (json.loads(line) for line in file)
        agent_history, model_history = zip(*decoded_lines)

    flattened_agent_history = []
    for step, agents in enumerate(agent_history):
        for agent in agents:
            flattened_agent_history.append({"step": step, **agent})

    agent_history_df = pd.DataFrame(flattened_agent_history)
    model_history_df = (
        pd.DataFrame(model_history).reset_index().rename({"index": "step"}, axis=1)
    )
    return agent_history_df, model_history_df
