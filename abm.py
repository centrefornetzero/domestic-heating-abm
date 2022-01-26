import functools
import json
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TextIO,
    Tuple,
    TypeVar,
)

import pandas as pd
import structlog

A = TypeVar("A", bound="Agent")
M = TypeVar("M", bound="AgentBasedModel")
T = TypeVar("T")
History = Iterable[Tuple[List[Dict[str, Any]], Dict[str, Any]]]


logger = structlog.getLogger()


class UnorderedSpace(Generic[A]):
    def __init__(self) -> None:
        self.agents: Dict[A, None] = dict()

    def add_agent(self, agent: A) -> None:
        self.agents[agent] = None

    def __contains__(self, agent: A) -> bool:
        return agent in self.agents

    def __iter__(self) -> Iterator[A]:
        yield from self.agents


class Agent:
    def make_decisions(self, model: Optional["AgentBasedModel"] = None) -> None:
        raise NotImplementedError


class AgentBasedModel(Generic[A]):
    def __init__(self, space: Optional[UnorderedSpace[A]] = None) -> None:
        self.space = space if space else UnorderedSpace[A]()

    def add_agent(self, agent: A) -> None:
        self.space.add_agent(agent)

    def add_agents(self, agents: Iterable[A]) -> None:
        for agent in agents:
            self.add_agent(agent)

    def increment_timestep(self) -> None:
        raise NotImplementedError

    def run(
        self,
        time_steps: int,
        agent_callables: Optional[List[Callable[[A], Any]]] = None,
        model_callables: Optional[List[Callable[["AgentBasedModel[A]"], Any]]] = None,
    ) -> History:
        if agent_callables is None:
            agent_callables = []

        if model_callables is None:
            model_callables = []

        for step in range(time_steps):
            start_time = time.time()

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

            logger.info(
                "step completed",
                step=step,
                elapsed_time_seconds=time.time() - start_time,
            )

            yield agent_data, model_data


def collect_when(
    model: M, condition: Callable[[M], bool]
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


def write_jsonlines(history: History, file: TextIO) -> None:
    for step in history:
        file.write(json.dumps(step, default=str) + "\n")


def read_jsonlines(file: TextIO) -> History:
    for line in file:
        yield tuple(json.loads(line))  # type: ignore


def history_to_dataframes(history: History) -> Tuple[pd.DataFrame, pd.DataFrame]:
    agent_history, model_history = zip(*history)

    flattened_agent_history = []
    for step, agents in enumerate(agent_history):
        for agent in agents:
            flattened_agent_history.append({"step": step, **agent})

    agent_history_df = pd.DataFrame(flattened_agent_history)
    model_history_df = (
        pd.DataFrame(model_history).reset_index().rename({"index": "step"}, axis=1)
    )
    return agent_history_df, model_history_df
