FROM python:3.9.6-slim-buster AS dependencies

RUN apt-get update && apt-get -y upgrade

RUN pip install pipenv
ENV PIPENV_VENV_IN_PROJECT=1

RUN useradd --create-home user && chown -R user /home/user
USER user
WORKDIR /home/user/src

COPY --chown=user Pipfile* .
RUN pipenv sync
ENV PATH="/home/user/src/.venv/bin:$PATH"
ENV PYTHONPATH=.
ENV PYTHONHASHSEED=0


FROM dependencies AS runtime

COPY --chown=user . .
ENTRYPOINT ["python", "-m", "simulation"]


FROM dependencies AS testrunner

RUN pipenv sync --dev
ENV PYTEST_ADDOPTS="-p no:cacheprovider"
COPY --chown=user . .
CMD ["pytest"]
