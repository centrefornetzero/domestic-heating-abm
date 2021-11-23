# python-template

Centre for Net Zero's template for Python projects.

Tools:

* [Pipenv](https://github.com/pypa/pipenv) for dependency management
* [Pytest](https://github.com/pytest-dev/pytest/) for testing
* [Mypy](https://mypy.readthedocs.io/en/stable/) for type checking
* [Flake8](https://flake8.pycqa.org/en/latest/) for linting
* [isort](https://github.com/PyCQA/isort) and [black](https://github.com/psf/black) for formatting

There are two Github Actions workflows:

* `test_and_lint.yaml` runs checks on a Ubuntu Github-hosted runner.
* `container.yaml` runs the same checks but inside a Docker container and pushes images to [Google Cloud Platform Artifact Registry](https://cloud.google.com/artifact-registry).

## Secrets configuration

If you want to use the Docker workflow, you need to set the following secrets:

* `GCP_ARTIFACT_REGISTRY`, e.g. `LOCATION-docker.pkg.dev/PROJECT-ID`
* `GCP_ARTIFACT_REGISTRY_SA_KEY`, the key for a service account with the roles to push and pull images.

## Python Setup

You need to [set up your Python environment](https://docs.google.com/document/d/1Tg0eKalqOp-IJEeH7aShc9fYF5zn95H6jxEk25BLLUE/) first.

1. Clone this repo.
2. `pipenv sync --dev` to install dependencies.
3. `cp .env.template .env` and fill in any blanks.
4. `pipenv run pytest`
