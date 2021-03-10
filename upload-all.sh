#!/bin/bash

if [[ ! -v TERMSERVER_ENDPOINT ]]; then
  echo "TERMSERVER_ENDPOINT is not set, set the environment variable to the FHIR endpoint of the terminology server"
  echo "e.g. export TERMSERVER_ENDPOINT=http://localhost:8080/fhir"
  exit 1
else
  echo "using the following terminology/FHIR endpoint: $TERMSERVER_ENDPOINT"
fi

if ! command -v fhir &> /dev/null; then
  echo "fhir (Firely Terminal, https://simplifier.net/downloads/firely-terminal) could not be found"
  exit 3
fi
if ! command -v jq &> /dev/null; then
  echo "jq (https://stedolan.github.io/jq/) could not be found"
  exit 3
fi

upload_all_json_from_dir () {
  pushd $1
  for f in *.json; do 
    echo $f
    fhir put $TERMSERVER_ENDPOINT $f
  done
  popd
}

enter_to_continue () {
  read -p "Press enter to continue, CTRL-C to cancel"
  printf "\n\n######\n\n"
}

echo "step 0: make sure the ArtDecor exports are converted to FHIR and put in ./data/output-cs (you can use the convert-all script for that)"

# read -p "Press enter to continue, CTRL-C to cancel"
# echo "\n\n######\n\n"
enter_to_continue

echo "step 1: uploading referenced IHE code systems, from data/output-cs"
# pushd data/output-cs
# for f in *.json; do 
#   echo $f
#   fhir put $TERMSERVER_ENDPOINT $f
# done
# popd
upload_all_json_from_dir "data/output-cs"

enter_to_continue
echo "step 2: uploading referenced external code systems"
upload_all_json_from_dir "data/referenced-resources/CodeSystem"

enter_to_continue
echo "step 3: uploading referenced external value sets"
upload_all_json_from_dir "data/referenced-resources/ValueSet"

enter_to_continue
echo "step 4: uploading all ValueSets"
upload_all_json_from_dir "data/input-data/fhir-vs/json"

enter_to_continue
echo "step 5: expanding all ValueSets using the test script"
pushd data/test-script
./expand-all-vs.sh > expand-all.log
echo "the log is at data/test-script/expand-all.log"
read -p "Press enter to open it using Less, ctrl-C to quit (we are done otherwise). Less can be exited with q or ctrl-c"
less expand-all.log
popd

