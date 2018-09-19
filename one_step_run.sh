#!/usr/bin/env bash

if ! [ $# -eq 1 ]
  then
    echo "No arguments supplied"
    echo "usage: one_step_run.sh <use_case>"
    echo "accepted use_case can be \"scrapezacks\", \"scrapezacks_to_remote\",\"email_content01\"."
    exit 1
fi

if [ -z "$(command -v chromedriver)" ]; then
  echo "chromedriver is not available in PATH. Now exists."
  exit 1
fi

python_path=$(command -v python)
if [[ ${python_path} = *"/venv/bin/python" ]]; then
  echo "parent terminal already in venv."
else
  echo "parent terminal not in venv. Going to enter venv"
  source ./venv/bin/activate
fi
pip3 install -r ./requirements.txt > /dev/null
python3 src/main/python/main.py "$1"