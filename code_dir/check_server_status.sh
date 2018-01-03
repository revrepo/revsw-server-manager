#!/usr/bin/env bash


export PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
$PROJECT_DIR/.env/bin/python $PROJECT_DIR/check_server_status.py $*
