#!/bin/bash

ssh openhabian@192.168.1.61 << EOF
cd /home/openhabian/domino_hub
git pull
./release.sh
EOF
