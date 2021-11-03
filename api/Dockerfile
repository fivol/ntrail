FROM python:3.9

RUN pip install "poetry"
WORKDIR /app
COPY . .

RUN ./run.sh

RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

CMD [ "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000" ]