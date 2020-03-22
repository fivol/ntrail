#!/bin/bash
sudo rm -rf app
cp -r ../backend .
mv backend app

git add .
git commit -m"docker auto"
git push origin docker

ssh root@95.182.122.120 #cd /app/NTrail && echo $PWD && git pull 
#&& git checkout docker && docker-compose down && docker-compose build --no-cache && docker-compose start && exit

echo Done upload!











