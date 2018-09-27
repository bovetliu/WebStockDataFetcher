#!/usr/bin/env bash

exit_if_not_zero () {
  if ! [ $2 -eq 0 ]; then
    echo "[seed_database.sh] $1 exited with status $2. $0 going to fail."
    exit 1
  fi
}

if [ ! -d "./data" ]; then
  mkdir ./data
fi

if [ ! -f ./credentials ]; then
    echo "./credentials file is not found"
    exit 9
fi

if ! [ $# -eq 1 ]
  then
    echo "No arguments supplied"
    echo "usage: one_step_run.sh <use_case>"
    echo "accepted use_case can be \"scrapezacks\", \"scrapezacks_to_remote\",\"email_content01\"."
    exit 1
fi

if [ -z "$(command -v chromedriver)" ]; then
  echo "chromedriver is not available in PATH. Now exists."
  exit 3
fi

python_path=$(command -v python3)
if [[ ${python_path} = *"/venv/bin/python3" ]]; then
  echo "parent terminal already in venv."
else
  if [ ! -d "./venv" ]; then
    python3 -m venv ./venv
    temp_exit_val=$?
    sleep 5
    exit_if_not_zero "creat_venv" ${temp_exit_val}
  fi
  echo "parent terminal not in venv. Going to enter venv"
  source ./venv/bin/activate
  exit_if_not_zero "activate venv" $?
fi
pip3 install --upgrade pip
pip3 install -r ./requirements.txt > /dev/null
exit_if_not_zero "pip install requirements" $?
python3 src/main/python/main.py "$1"