FROM python:3.9

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-dependencies --upgrade pip --ignore-installed -r ./requirements.txt
COPY . .
CMD [ "python", "./main.py" ]
