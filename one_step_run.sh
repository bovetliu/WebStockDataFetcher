#!/usr/bin/env bash

exit_if_not_zero () {
  if ! [ $2 -eq 0 ]; then
    echo "[one_step_run.sh] $1 exited with status $2. $0 going to fail."
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

if [ "$#" -gt 3 ] || [ "$#" -lt 1 ]
  then
    echo "Number of arguments incorrect"
    echo "usage: one_step_run.sh <use_case> <optional_database_name: default zacks>"
    echo "accepted use_case can be \"scrapezacks\", \"scrapezacks_to_remote\",\"email_content01\"."
    echo "acceptable database_name: any valid MySQL database name"
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
python3 src/main/python/main.py "$1" "$2"

echo "last argument: ${@: -1}"
if [ "${@: -1}" = "shutdown_after_execution" ]; then
  if [ ${USER} != "ubuntu" ]; then
    echo "It is like not running in AWS, because \$USER is not \"ubuntu\", will abort shutdown."
    exit 9
  fi
  echo "going to shutdown instance in 1 minute."
  sudo shutdown -h +1
fi

# triggered by cloudwatch event
# 0/20 13-22 ? * MON-FRI *
# input {"region": "us-east-2", "operation": "start_instances"}