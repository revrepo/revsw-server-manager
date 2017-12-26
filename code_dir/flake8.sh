#!/bin/bash

status=0

echo "run flake8"
flake8

status_1=$?
if [ $status_1 -ne 0 ]
then
    status=1
fi
exit $status
