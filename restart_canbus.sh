#!/bin/bash

/sbin/ifconfig can0 down
/sbin/ifconfig can0 up

#/sbin/ifconfig can1 down
#/sbin/ifconfig can1 up

echo `date` > /tmp/hi.txt

exit 0
