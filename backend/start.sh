#!/bin/bash

sudo apt update
sudo apt upgrade

sudo apt install -y docker
sudo apt install -y docker-compose

echo Docker installation done!

docker-compose up
