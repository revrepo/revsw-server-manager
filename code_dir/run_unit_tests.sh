#!/bin/bash

status=0


echo "coverage run -t server_deployment/tests.py"
coverage run server_deployment/tests.py
status_1=$?
if [ $status_1 -ne 0 ]
then
    status=1
fi
coverage report
exit $status
