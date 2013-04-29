#!/bin/bash

if [ -f /etc/node_status/reboot_event ]
then
    cat /etc/node_status/reboot_event | while read line
    do
        echo "EVENT:$line"
    done
fi
