import datetime

from simulation.collectors import is_first_step
from simulation.tests.common import model_factory


def test_is_first_step() -> None:
    step_interval = datetime.timedelta(days=1)
    model = model_factory(
        start_datetime=datetime.datetime.now(), step_interval=step_interval
    )
    assert not is_first_step(model)

    model.increment_timestep()
    assert is_first_step(model)

    model.increment_timestep()
    assert not is_first_step(model)
