#!/bin/bash

status=0

. "./.env/bin/activate"
echo "coverage run -t server_deployment/tests.py"
export PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
coverage run  --source=$PROJECT_DIR --omit=$PROJECT_DIR/.env/lib/* server_deployment/tests.py
status_1=$?
if [ $status_1 -ne 0 ]
then
    status=1
fi
coverage report
exit $status
