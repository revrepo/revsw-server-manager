#!/bin/bash

export PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
$PROJECT_DIR/env/bin/python $PROJECT_DIR/rs.py $*
