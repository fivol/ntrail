FROM python:3.9

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip --ignore-installed -r ./requirements.txt
EXPOSE 5432
COPY . .
CMD [ "python", "./main.py" ]
