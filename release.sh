#!/bin/bash

set -e

DST=/opt/stacks/hass/config/custom_components/domino_hub
sudo mkdir -p ${DST}
sudo cp *.py ${DST}/
sudo cp *.json ${DST}/
ls -al ${DST}/