#!/bin/bash
sudo rm -rf app
cp -r ../backend .
mv backend app

git add .
git commit -m"docker auto"
git push origin docker

#ssh root@95.182.122.120 "/app/NTrail/pull.sh"
ssh root@95.182.122.120 "cd /app/NTrail && git pull && docker-compose build --no-cache && docker-compose down && docker-compose up"

echo Done upload!











