import datetime

import pandas as pd
import pytest

from abm import (
    Agent,
    AgentBasedModel,
    History,
    UnorderedSpace,
    collect_when,
    read_jsonlines,
    write_jsonlines,
)


class TestAgentBasedModel:
    def test_create_abm_with_properties(self) -> None:
        properties = {"a": 1, "b": 2}
        model = AgentBasedModel(**properties)
        assert model.a == 1
        assert model.b == 2

    def test_add_agent_to_abm(self) -> None:
        model = AgentBasedModel()
        agent = Agent()
        model.add_agent(agent)
        assert agent in model.space

    def test_add_agents_to_abm(self) -> None:
        model = AgentBasedModel()
        agents = [Agent(), Agent(), Agent()]
        model.add_agents(agents)
        for agent in agents:
            assert agent in model.space

    def test_run_yields_agent_and_model_data_at_each_step(self) -> None:
        class CountingABM(AgentBasedModel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.counter = 0

            def step(self):
                self.counter += 1

        model = CountingABM()

        class CountingAgent(Agent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.counter = 0

            def make_decisions(self, model=None):
                self.counter += 1

        num_agents = 3
        model.add_agents([CountingAgent() for _ in range(num_agents)])

        def agent_counter(agent):
            return agent.counter

        def model_counter(model):
            return model.counter

        time_steps = 3
        history = model.run(time_steps, [agent_counter], [model_counter])

        for step_num, step in enumerate(history):
            agents, model = step
            assert len(agents) == num_agents
            for agent in agents:
                assert agent["agent_counter"] == step_num + 1

            assert model["model_counter"] == step_num + 1

    def test_run_yields_data_if_agent_callable_evaluates_to_false(self) -> None:
        class HouseholdAgent(Agent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.empty_value = None
                self.bool_value = False

            def make_decisions(self, model=None):
                pass

        def agent_callable_returning_none(agent):
            return agent.empty_value

        def agent_callable_returning_false(agent):
            return agent.bool_value

        model = AgentBasedModel()
        model.add_agents([HouseholdAgent(), HouseholdAgent(), HouseholdAgent()])
        time_steps = 10

        history = model.run(
            time_steps=time_steps, agent_callables=[agent_callable_returning_none]
        )

        for step_num, step in enumerate(history):
            agents, _ = step
            for agent in agents:
                assert agent == {}

        history = model.run(
            time_steps=time_steps, agent_callables=[agent_callable_returning_false]
        )

        for step_num, step in enumerate(history):
            agents, _ = step
            for agent in agents:
                assert agent == {"agent_callable_returning_false": False}


def test_collect_when() -> None:
    class DateABM(AgentBasedModel):
        def __init__(self, start_date: datetime.date, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.date = start_date

        def step(self):
            self.date += datetime.timedelta(days=1)

    start_date = datetime.date(2021, 9, 20)
    assert start_date.weekday() == 0
    model = DateABM(start_date)

    class CountingAgent(Agent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.counter = 0

        def make_decisions(self, model=None):
            self.counter += 1

    model.add_agent(CountingAgent())

    def week_end(model: AgentBasedModel) -> bool:
        return model.date.weekday() == 6

    @collect_when(model, week_end)
    def agent_counter(agent: Agent) -> bool:
        return agent.counter

    time_steps = 30
    history = model.run(time_steps, agent_callables=[agent_counter])
    agent_history, _ = zip(*history)

    assert len(agent_history) == steps
    assert [agent for step in agent_history for agent in step if agent] == [
        {"agent_counter": 6},
        {"agent_counter": 13},
        {"agent_counter": 20},
        {"agent_counter": 27},
    ]


class TestAgent:
    def test_step_is_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            Agent().step()


class TestUnorderedSpace:
    def test_add_agent(self) -> None:
        space = UnorderedSpace()
        agent = Agent()
        space.add_agent(agent)
        assert agent in space

    def test_iterating_over_space_returns_agents(self) -> None:
        space = UnorderedSpace()
        agents = {Agent(), Agent(), Agent()}
        for agent in agents:
            space.add_agent(agent)

        assert set(space) == agents


def test_write_jsonlines_output_and_read_into_dataframe(tmp_path) -> None:
    today = datetime.date.today()
    history: History = [
        ([{"agent": 1}, {"agent": 2}], {"date": today, "attribute": "a"}),
        ([{"agent": 3}, {"agent": 4}], {"date": today, "attribute": "b"}),
    ]
    filename = str(tmp_path / "filename.jsonl")

    write_jsonlines(history, filename)
    agent_history, model_history = read_jsonlines(filename)

    pd.testing.assert_frame_equal(
        agent_history,
        pd.DataFrame({"step": [0, 0, 1, 1], "agent": [1, 2, 3, 4]}),
    )
    pd.testing.assert_frame_equal(
        model_history,
        pd.DataFrame(
            {"step": [0, 1], "date": [str(today), str(today)], "attribute": ["a", "b"]},
        ),
    )
