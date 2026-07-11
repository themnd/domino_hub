#!/bin/bash

COMMIT_ID=$(git rev-parse --short HEAD)
echo "Deploying commit: $COMMIT_ID"

ssh -t openhabian@192.168.1.61 "cd /home/openhabian/domino_hub && git pull && echo $COMMIT_ID > version.txt && ./release.sh"
TOKEN=$(cat "$(dirname "$0")/token.txt")
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    "http://1bs8mxtwoevlqho3.myfritz.net:8123/api/services/homeassistant/restart"
echo "Home Assistant restarting..."
