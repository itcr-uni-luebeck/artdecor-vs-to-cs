#!/bin/bash

if [[ ! -v TERMSERVER_ENDPOINT ]]; then
  echo "TERMSERVER_ENDPOINT is not set, set the environment variable to the FHIR endpoint of the terminology server (without trailing /)"
  exit 1
fi
if ! command -v jq &> /dev/null; then
  echo "jq (https://stedolan.github.io/jq/) could not be found"
  exit 2
fi

#download the list of valuesets on the server to file
curl -s -H "Accept=application/json" $TERMSERVER_ENDPOINT/ValueSet > valuesets.json

#reshape the received bundle, so that we get a pretty list of canonicals, names, ids, resource urls, and expansions
#normally, jq outputs ndjson (unless filtering with '[...complex filter...]'), so output both ndjson and array-json (by slurping all ndjson lines)
jq '.entry[] | {canonical: (.resource.url), name: (.resource.name), id: (.resource.id), resource: (.fullUrl), expansion: ("$TERMSERVER_ENDPOINT/ValueSet/$expand?_format=json&url=" + (.resource.url))}' valuesets.json > ihe-valueset-list.ndjson
jq -s "." ihe-valueset-list.ndjson > ihe-valueset-list.json

#list all the canonical urls for the valuesets
canonicals=`jq -r ".entry[].resource.url" valuesets.json`

#expand each valueset using the respective url
for c in $canonicals; do
  echo "canonical: $c"
  url="$TERMSERVER_ENDPOINT/ValueSet/\$expand?url=$c&_format=json"
  echo "expansion: $url"
  #piping to jq formats JSON nicely
  #output is put on stdout -> redirect the output somewhere!
  curl -s $url | jq "."
  echo
done
