#!/bin/bash

git pull
git checkout docker
docker-compose build --no-cache
docker-compose down
docker-compose start
