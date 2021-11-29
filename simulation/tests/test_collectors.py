import datetime

from simulation.collectors import is_first_step
from simulation.model import CnzAgentBasedModel


def test_is_first_step() -> None:
    step_interval = datetime.timedelta(days=1)
    model = CnzAgentBasedModel(datetime.datetime.now(), step_interval)
    assert not is_first_step(model)

    model.step()
    assert is_first_step(model)

    model.step()
    assert not is_first_step(model)
