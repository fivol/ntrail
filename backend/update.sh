#!/bin/bash


git pull &&
docker-compose stop &&
docker-compose build &&
docker-compose up -d &&

echo App updated successfully!











