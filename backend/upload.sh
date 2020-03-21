#!/bin/bash
rm -r app
mkdir app
cp ../backend app

git add .
git commit -m"docker auto"
git push origin docker

ssh root@95.182.122.120

cd /app/NTrail

git pull
git checkout docker

docker-compose restart

echo Done upload!
