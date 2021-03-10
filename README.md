# IHE ArtDecor ValueSet Conversion

Python script and data for extracting the codes contained in the IHE ValueSets for XDS.

## Python script

The script was written in Python 3 and requires some run-time dependencies. You should use a UNIX-based system or Windows Subsystem for Linux for this script.

To run, please set up a virtual environment like so:

```bash
python -m venv .venv
source .venv/bin/activate
```

Next, install the runtime dependencies like so:

```bash
pip install -r requirements.txt
```

Afterwards, you can build the script using setuptools:

```bash
pip install --editable .
```

You should now be able to run the script from the command line:

```bash
artdecorvsconvert
```

You will also need [Firely Terminal]() and [JQ]() installed and available on the PATH for the shell sscripts to work.

## Data in this repository

```
.
├── artdecorvsconvert.py - the python script itself
├── convert-all.sh - invoke the python script for a list of files with identical settings
├── data - contains the required data for the IHE value sets
│   ├── input-data - data from ArtDecor
│   │   ├── art-decor-format - an export of each value set in the ArtDecor native format (JSON)
│   │   │   ├── Codessozialgesetzbuch.json
│   │   │   ├── IHEXDSauthorRole_v2.json
│   │   │   └── ...
│   │   └── fhir-vs - the ArtDecor Valuesets in FHIR
│   │       ├── json - converted from the XML export using Firely Terminal (fhir put $f; fhir save $f.json)
│   │       │   ├── upload.sh - upload all the ValueSets to a terminology server and expand them for verification purposes
│   │       │   ├── ValueSet-1.2.276.0.76.11.30--20180713131246.xml.json
│   │       │   ├── ValueSet-1.2.276.0.76.11.31--20180713132208.xml.json
│   │       │   └── ...
│   │       └── xml - the ValueSets as exported from ArtDecor/Simplifier
│   │           ├── ValueSet-1.2.276.0.76.11.30--20180713131246.xml
│   │           ├── ValueSet-1.2.276.0.76.11.34--20201002134255.xml - this file was modified because of a logical error
│   │           ├── ValueSet-1.2.276.0.76.11.34--20201002134255.xml.original - the original version of the above file
│   │           └── ...
│   ├── output-cs - the extracted FHIR CodeSystems as exported by the python tool
│   │   ├── cs-1.2.276.0.76.5.114-v2.fhir.json
│   │   ├── cs-1.2.276.0.76.5.509-v2.fhir.json
│   │   └── ...
│   ├── referenced-resources - resources that are needed for ValueSet expansion, which have not been defined by IHE
│   │   ├── CodeSystem - FHIR CodeSystems that are referenced
│   │   │   ├── codesystem-dicom-dcim.json - The DICOM DCIM ontology, downloaded from FHIR Terminology
│   │   │   ├── CodeSystem-formatcode.json - the IHE Format Codes from the IHE-defined profile, with changed canonical URL
│   │   │   ├── CodeSystem-formatcode.json.original - the IHE Format Codes from the IHE-defined profile, original
│   │   │   ├── CodeSystem-v3-Confidentiality.json - from https://terminology.hl7.org/2.1.0/CodeSystem-v3-Confidentiality.html
│   │   │   └── dicom-uids.json - converted from the DICOM specification
│   │   ├── DICOM-UIDs - the registry of DICOM UIDs, refer to the README.md in this dir
│   │   │   ├── ARegistryOfDICOMUniqueIdentifiers(UIDs)(Normative).html
│   │   │   ├── ARegistryOfDICOMUniqueIdentifiers(UIDs)(Normative)_table.csv
│   │   │   ├── ARegistryOfDICOMUniqueIdentifiers(UIDs)(Normative)_table.html
│   │   │   ├── ARegistryOfDICOMUniqueIdentifiers(UIDs)(Normative)_table.ods
│   │   │   └── README.md
│   │   └── ValueSet - referenced ValueSets, refer to README.md
│   │       ├── DICOM-CID_29.json
│   │       ├── DICOM-CID_4.json
│   │       └── README.md
│   └── test-script - a test script to expand all ValueSets on a term server
│       └── expand-all-vs.sh - the test script
├── requirements.txt - the requirements for the script in PyPI format - install with `pip install -r requirements.txt`
├── setup.py - the setup script for setuptools, install the script with `pip install --editable .`
├── upload-all.sh - a script to upload all resources to a FHIR Terminology server
└── value-set-oids.yml - a text file describing the ValueSets with referenced CodeSystems
```
