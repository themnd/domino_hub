#!/bin/bash

ssh -t openhabian@192.168.1.61 "cd /home/openhabian/domino_hub && git pull && ./release.sh"
