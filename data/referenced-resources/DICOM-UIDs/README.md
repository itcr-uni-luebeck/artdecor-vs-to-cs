# DICOM UID ValueSets

NEMA provides a list of assigned UIDs/OIDs as part of the DICOM specification, available at http://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_A.html in CHTML format.

This file was downloaded as HTML and processed to only include the table "A-1" using a text editor. CSS references were stripped as well. The dowload was done on 2021-03-09. Some non-printable characters that were present in the downloaded HTML file were removed. 

After processing the file like so, it was opened using LibreOffice Calc. Links were stripped from the column "part". Another column was added using a formula that provides the "deprecated" property.

This sheet was saved as ODS and exported to CSV. This CSV file was using for creating the FHIR resource using CSIRO's Snapper tool (http://ontoserver.csiro.au/snapper/index.html). A new code system was created with the respective metadata. New properties `uidType`, `dicomPart` and `deprecated` were created using String, String, and Boolean types respectively.

Then, the exported CSV file was uploaded to the Snapper tool. The columns were mapped to the respective properties (UID - Code, UID Name - Definition, UID Keyword - Display, Type - uidType property, Part - dicomPart property, Deprecated - deprecated property).

This FHIR CodeSystem was exported and is available in this repository at `../CodeSystem/dicom-uids.json`
