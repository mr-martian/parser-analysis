#!/bin/bash

# https://stackoverflow.com/questions/59895/how-can-i-get-the-directory-where-a-bash-script-is-located-from-within-the-scrip
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" udapy -qs .constructions.Constructions
