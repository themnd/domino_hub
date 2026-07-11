#!/bin/bash

ssh -t openhabian@192.168.1.61 "cd /home/openhabian/domino_hub && git pull && ./release.sh"
TOKEN=$(cat "$(dirname "$0")/token.txt")
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    "http://1bs8mxtwoevlqho3.myfritz.net:8123/api/services/homeassistant/restart"
 echo "Home Assistant restarting..."
