import datetime
import pathlib
from typing import Optional

import pandas as pd
import pytest

from abm import (
    Agent,
    AgentBasedModel,
    History,
    UnorderedSpace,
    collect_when,
    history_to_dataframes,
    read_jsonlines,
    write_jsonlines,
)


class TestAgentBasedModel:
    def test_add_agent_to_abm(self) -> None:
        model = AgentBasedModel[Agent]()
        agent = Agent()
        model.add_agent(agent)
        assert agent in model.space

    def test_add_agents_to_abm(self) -> None:
        model = AgentBasedModel[Agent]()
        agents = [Agent(), Agent(), Agent()]
        model.add_agents(agents)
        for agent in agents:
            assert agent in model.space

    def test_run_yields_agent_and_model_data_at_each_step(self) -> None:
        class CountingAgent(Agent):
            def __init__(self) -> None:
                super().__init__()
                self.counter = 0

            def make_decisions(self, model: Optional[AgentBasedModel] = None) -> None:
                self.counter += 1

        class CountingABM(AgentBasedModel[CountingAgent]):
            def __init__(self) -> None:
                super().__init__()
                self.counter = 0

            def increment_timestep(self) -> None:
                self.counter += 1

        model = CountingABM()

        num_agents = 3
        model.add_agents([CountingAgent() for _ in range(num_agents)])

        def agent_counter(agent: CountingAgent) -> int:
            return agent.counter

        def model_counter(model: AgentBasedModel) -> Optional[int]:
            return getattr(model, "counter", None)

        time_steps = 3
        history = model.run(time_steps, [agent_counter], [model_counter])

        for step_num, step in enumerate(history):
            agent_histories, model_history = step
            assert len(agent_histories) == num_agents
            for agent in agent_histories:
                assert agent["agent_counter"] == step_num + 1

            assert model_history["model_counter"] == step_num + 1

    def test_run_yields_data_if_agent_callable_evaluates_to_false(self) -> None:
        class HouseholdAgent(Agent):
            def __init__(self) -> None:
                super().__init__()
                self.empty_value = None
                self.bool_value = False

            def make_decisions(
                self, model: Optional["AgentBasedModel[HouseholdAgent]"] = None  # noqa
            ) -> None:
                pass

        def agent_callable_returning_none(agent: HouseholdAgent) -> None:
            return agent.empty_value

        def agent_callable_returning_false(agent: HouseholdAgent) -> bool:
            return agent.bool_value

        model = AgentBasedModel[HouseholdAgent]()
        model.add_agents([HouseholdAgent(), HouseholdAgent(), HouseholdAgent()])
        time_steps = 10

        history = model.run(
            time_steps=time_steps, agent_callables=[agent_callable_returning_none]
        )

        for step in history:
            agents, _ = step
            for agent in agents:
                assert agent == {}

        history = model.run(
            time_steps=time_steps, agent_callables=[agent_callable_returning_false]
        )

        for step in history:
            agents, _ = step
            for agent in agents:
                assert agent == {"agent_callable_returning_false": False}


def test_collect_when() -> None:
    class DateABM(AgentBasedModel):
        def __init__(self, start_date: datetime.date) -> None:
            super().__init__()
            self.date = start_date

        def increment_timestep(self) -> None:
            self.date += datetime.timedelta(days=1)

    start_date = datetime.date(2021, 9, 20)
    assert start_date.weekday() == 0
    model = DateABM(start_date)

    class CountingAgent(Agent):
        def __init__(self) -> None:
            super().__init__()
            self.counter = 0

        def make_decisions(
            self, model: Optional[AgentBasedModel["CountingAgent"]] = None  # noqa
        ) -> None:
            self.counter += 1

    model.add_agent(CountingAgent())

    def week_end(model: DateABM) -> bool:
        return model.date.weekday() == 6

    @collect_when(model, week_end)
    def agent_counter(agent: CountingAgent) -> int:
        return agent.counter

    time_steps = 30
    history = model.run(time_steps, agent_callables=[agent_counter])
    agent_history, _ = zip(*history)

    assert len(agent_history) == time_steps
    assert [agent for step in agent_history for agent in step if agent] == [
        {"agent_counter": 6},
        {"agent_counter": 13},
        {"agent_counter": 20},
        {"agent_counter": 27},
    ]


class TestAgent:
    def test_make_decisions_is_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            Agent().make_decisions()


class TestUnorderedSpace:
    def test_add_agent(self) -> None:
        space = UnorderedSpace[Agent]()
        agent = Agent()
        space.add_agent(agent)
        assert agent in space

    def test_iterating_over_space_returns_agents(self) -> None:
        space = UnorderedSpace[Agent]()
        agents = {Agent(), Agent(), Agent()}
        for agent in agents:
            space.add_agent(agent)

        assert set(space) == agents


def test_write_and_read_jsonlines_output(tmp_path: pathlib.Path) -> None:
    today = datetime.date.today().isoformat()
    history: History = [
        ([{"agent": 1}, {"agent": 2}], {"date": today, "attribute": "a"}),
        ([{"agent": 3}, {"agent": 4}], {"date": today, "attribute": "b"}),
    ]
    filename = str(tmp_path / "filename.jsonl")

    with open(filename, "w") as file:
        write_jsonlines(history, file)

    with open(filename, "r") as file:
        deserialized_history = list(read_jsonlines(file))

    assert history == deserialized_history


def test_history_to_dataframe() -> None:
    today = datetime.date.today().isoformat()
    history: History = [
        ([{"agent": 1}, {"agent": 2}], {"date": today, "attribute": "a"}),
        ([{"agent": 3}, {"agent": 4}], {"date": today, "attribute": "b"}),
    ]

    agent_history_df, model_history_df = history_to_dataframes(history)

    pd.testing.assert_frame_equal(
        agent_history_df,
        pd.DataFrame({"step": [0, 0, 1, 1], "agent": [1, 2, 3, 4]}),
    )
    pd.testing.assert_frame_equal(
        model_history_df,
        pd.DataFrame(
            {"step": [0, 1], "date": [str(today), str(today)], "attribute": ["a", "b"]},
        ),
    )
