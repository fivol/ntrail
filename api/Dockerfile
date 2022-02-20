FROM python:3.9

RUN pip install "poetry"
WORKDIR /app
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

COPY prepare.sh prepare.sh
RUN ./prepare.sh

CMD [ "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" ]