#!/bin/bash
sudo rm -rf app
mkdir app
cp -r ../backend ./app

git add .
git commit -m"docker auto"
git push origin docker

ssh root@95.182.122.120 cd /app/NTrail && git pull && git checkout docker && docker-compose restart && exit

echo Done upload!











