FROM python:3.9
WORKDIR /app
RUN pip install poetry
RUN poetry install

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]