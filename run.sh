#!/bin/bash

sleep 2
python3 /home/pi/run2.py &> /home/pi/logs/`date +%F_%H-%M-%S`.log
