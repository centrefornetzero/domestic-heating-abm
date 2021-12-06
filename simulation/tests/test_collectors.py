import datetime

from simulation.collectors import is_first_step
from simulation.model import CnzAgentBasedModel


def model_factory(**model_attributes):
    default_values = {
        "start_datetime": datetime.datetime.now(),
        "step_interval": datetime.timedelta(minutes=1440),
        "annual_renovation_rate": 0.05,
        "household_num_lookahead_years": 3,
    }
    return CnzAgentBasedModel(**{**default_values, **model_attributes})


def test_is_first_step() -> None:
    step_interval = datetime.timedelta(days=1)
    model = model_factory(
        start_datetime=datetime.datetime.now(), step_interval=step_interval
    )
    assert not is_first_step(model)

    model.step()
    assert is_first_step(model)

    model.step()
    assert not is_first_step(model)
