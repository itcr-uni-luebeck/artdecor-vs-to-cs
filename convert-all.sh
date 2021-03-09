#!/bin/bash
if [[ ! $# -eq 1 ]]
then
  echo "need a path where the JSON files are"
  exit 1
fi
if ! command -v artdecorvsconvert &> /dev/null; then
  echo "The command artdecorvsconvert could not be found, please run the following commands (in a python virtual environment):"
  echo "pip install -r requirements.txt"
  echo "pip install --editable ."
  exit 2
fi

for f in $1/*.json
do 
  artdecorvsconvert --output-dir=./output --artdecor-from-file --artdecor $f
done
