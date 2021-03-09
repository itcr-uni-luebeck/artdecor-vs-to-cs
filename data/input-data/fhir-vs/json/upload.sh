#!/bin/bash

if [ $# -ne 1 ]; then 
  echo "missing file name"
  exit 1
fi

if [[ ! -v TERMSERVER_ENDPOINT ]]; then
  echo "TERMSERVER_ENDPOINT is not set, set the environment variable to the FHIR endpoint of the terminology server"
  exit 2
fi
if ! command -v fhir &> /dev/null; then
  echo "fhir (Firely Terminal, https://simplifier.net/downloads/firely-terminal) could not be found"
  exit 3
fi
if ! command -v jq &> /dev/null; then
  echo "jq (https://stedolan.github.io/jq/) could not be found"
  exit 3
fi

touch filelist.txt

canonical=`jq -r ".url" $1`
name=`jq -r ".name" $1`
echo "canonical URL: $canonical; name: $name" | tee -a upload.log

if grep -Fxq "$1" filelist.txt; then
  echo "file was already uploaded, press enter to continue, ctrl-c to quit"
  read -n1
  #exit 1
else 
  echo $1 >> filelist.txt
fi

cmd="fhir put $TERMSERVER_ENDPOINT $1"
echo $cmd
eval $cmd | tee -a upload.log
expansionurl="$TERMSERVER_ENDPOINT/ValueSet/\$expand?url=$canonical&_format=json"
echo $expansionurl | tee -a upload.log
curl $expansionurl | tee -a upload.log | jq "." | less
echo "\n\n" >> upload.log
