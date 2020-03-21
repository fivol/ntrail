#!/bin/bash

sudo apt update -y
sudo apt upgrade -y

sudo apt install -y docker
sudo apt install -y docker-compose

echo Docker installation done!

docker-compose start
