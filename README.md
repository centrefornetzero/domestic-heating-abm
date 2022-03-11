# Overview

Centre for Net Zero's Agent Based Model (ABM) for the electrification of heating. Currently under development - details to follow.

Our API design in `abm.py` follows a similar structure to [Agents.jl](https://juliadynamics.github.io/Agents.jl/stable/)
## Python Setup

You need to [set up your Python environment](https://docs.google.com/document/d/1Tg0eKalqOp-IJEeH7aShc9fYF5zn95H6jxEk25BLLUE/) first.

1. Clone this repo.
2. `pipenv sync --dev` to install dependencies.
3. `cp .env.template .env` and fill in any blanks.
4. `pipenv run pytest`
