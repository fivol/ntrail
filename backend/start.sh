#!/bin/bash

sudo apt update -y &&
sudo apt upgrade -y &&
sudo apt install apt-transport-https ca-certificates curl software-properties-common &&
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - &&
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" &&
sudo apt update -y &&
apt-cache policy docker-ce &&
sudo apt install -y docker-ce &&

sudo apt install -y docker-compose &&

echo Docker installation done! &&

docker-compose build &&
docker-compose up -d &&

echo Docker successfully launched!!!