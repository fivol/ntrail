#!/bin/bash

if [[ "$1" == "" || "$1" == "root@1.2.3.4" ]]; then
  echo -e "Please specify remote addr\nFor example:\n./upload.sh root@1.2.3.4"
  exit 1
fi;

ssh "$1" "cd ~/ntrail-backend && git pull && docker-compose down && docker-compose build && docker-compose up -d"

echo Done upload!
