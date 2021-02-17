from logging import error
from click.termui import prompt
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemConceptDesignation, CodeSystemConceptProperty, CodeSystemProperty, CodeSystemFilter
from fhir.resources.fhirtypes import IdentifierType
import requests
import click
import validators
import json
from typing import Dict, List, Union
import html
import re
from os import path
from datetime import date, datetime


class ArtDecorCodeSystem:
    oid: str
    name: str
    canonical: str

    def __init__(self, oid, name, canonical) -> None:
        self.oid = oid
        self.name = html.unescape(name.replace("&#160;", " "))
        self.canonical = canonical

    def __repr__(self) -> str:
        return f"CS[oid='{self.oid}', name='{self.name}', canonical='{self.canonical}']"


def canonical_for_code_system(jcs: Dict) -> str:
    """get the canonical URL for a code system entry from the art decor json. Prefer FHIR URIs over the generic OID URI.

    Args:
        jcs (Dict): the dictionary describing the code system

    Returns:
        str: the canonical URL
    """
    if "canonicalUriR4" in jcs:
        return jcs["canonicalUriR4"]
    else:
        return jcs["canonicalUri"]


def initialize_code_system(jcs: ArtDecorCodeSystem, version: str, vs_date: str) -> CodeSystem:
    """create a FHIR CodeSystem instance from the ArtDecor json description (with minimal data)

    Args:
        jcs (ArtDecorCodeSystem): the Art decor code system json
        version (str): the version (of the valueset) to use for the code system

    Returns:
        CodeSystem: the initialized R4 CodeSystem
    """
    dic = {
        "id": f"{jcs.oid}-{version}",
        "name": jcs.name,
        "url": jcs.canonical,
        "valueSet": f"{jcs.canonical}?vs",
        "identifier": [{
            "system": "urn:ietf:rfc:3986",
            "value": f"urn:oid:{jcs.oid}"
        }],
        "content": "complete",
        "status": "draft",
        "version": version,
        "date": vs_date,
        "concept": []
    }
    cs = CodeSystem(**dic)
    return cs


def filter_code_system(jcs: ArtDecorCodeSystem) -> bool:
    """decide if the code system is relevant to conversion. E.g. LOINC should not be generated from the ArtDecor ValueSets, but retrieved from the provider.

    Args:
        jcs (ArtDecorCodeSystem): the Art decor code system json

    Returns:
        bool: true if the cs should be filtered for conversion
    """
    filterable_oids = {"2.16.840.1.113883.6.1": "LOINC",
                       "2.16.840.1.113883.5.25": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality"}
    if jcs.oid in filterable_oids.keys():
        return True
    return False


def designation_for_ad_concept(adc: Dict) -> Dict:
    def get_display(desi):
        if "#text" in desi:
            return re.sub(r'&lt;.*&gt;', "", desi["#text"])
        elif "displayName" in desi:
            return desi["displayName"]
    if "desc" in adc:
        return [{
            "language": des["language"],
            "value": get_display(des)
        } for des in adc["desc"]]
    elif "designation" in adc:
        return [{
            "language": des["language"],
            "value": get_display(des)
        } for des in adc["designation"]]


def prompt_for_parent_code(concept: Dict, concept_list: List[Dict]) -> str:
    """prompt the user for the parent of a code that is marked as a leave -> the art decor json does not contain parentage information/is-a relationships!
    this methods makes the following assumptions: parent codes are from the same CS as the leave code, and parent codes don't have type "L" for "leaf"

    Args:
        code (str): the code to find the parent for
        concept (Dict): the concept that the parent should be found for
        concept_list (List[Dict]): the concepts in the ValueSet

    Returns:
        str: the code of the parent within the same code system
    """
    this_level = int(concept["level"])
    assert(this_level > 0)
    possible_specializable_concepts = [
        c for c in concept_list if c["type"] == "S"]
    possible_from_cs = [
        c for c in possible_specializable_concepts if c["codeSystem"] == concept["codeSystem"]]
    choices = [c for c in possible_from_cs if c["code"] !=
               concept["code"] and int(c["level"]) == this_level - 1]
    click.echo(
        f"\nParent for code='{concept['code']}' on level {this_level}, display='{concept['displayName']}'?")
    for i, choice in enumerate(choices):
        click.echo(
            f" [{i}] -> code='{choice['code']}', display='{choice['displayName']}'")
    if len(choices) == 1:
        chosen = choices[0]
        click.echo(f"using the only option with code='{chosen['code']}'")
    else:
        chosen = get_user_prompt(choices)
    return chosen["code"]


def get_user_prompt(choices: List[Dict], prompt: str = "your choice?") -> Dict:
    user_choice = -1
    while user_choice < 0:
        user_string_choice = click.prompt("your choice?")
        try:
            user_int_choice = int(user_string_choice)
        except:
            click.echo("not a valid choice")
            continue
        if user_int_choice < 0 or user_int_choice > len(choices):
            click.echo("not a valid choice")
        else:
            user_choice = user_int_choice
    return choices[user_choice]


def convert_to_fhir_codesystems(j: Dict):
    """convert the ArtDecor ValueSet to FHIR R4 code systems

    Args:
        j (Dict): the ArtDecor ValueSet dictionary
    """
    vs = j["valueSet"][0]
    vs_name = vs["name"]
    vs_oid = vs["id"]
    vs_version = vs["versionLabel"]
    vs_date = vs["effectiveDate"]
    click.echo(
        f"Converting the ValueSet '{vs_name}' (version '{vs_version}' with the OID {vs_oid})")
    all_present_code_systems = {x["id"]: ArtDecorCodeSystem(
        x["id"], x["identifierName"], canonical_for_code_system(x)) for x in vs["sourceCodeSystem"]}
    click.echo("The following code systems are present in the ValueSet:")
    click.echo(all_present_code_systems)
    present_code_systems = {
        oid: advs for oid, advs in all_present_code_systems.items() if not filter_code_system(advs)}
    click.echo("The following code systems should be converted:")
    click.echo(present_code_systems)

    fhir_code_systems = {
        oid:
        initialize_code_system(advs, vs_version, vs_date)
        for oid, advs in present_code_systems.items()
    }

    concept_list = vs["conceptList"][0]["concept"]
    for concept in concept_list:
        oid_of_code_system = concept["codeSystem"]
        dic = {
            "code": concept["code"],
            "display": concept["displayName"],
            "designation": designation_for_ad_concept(concept),
        }
        properties = []
        if concept["level"] != "0":
            parent_code = prompt_for_parent_code(concept, concept_list)
            properties.append({
                "code": "parent",
                "valueCode": parent_code
            })
        if concept["type"] == "D":
            properties.append({
                "code": "deprecated",
                "valueBoolean": False
            })
        if len(properties) > 0:
            concept["property"] = properties
        fhir_concept = CodeSystemConcept(**dic)
        fhir_code_systems[oid_of_code_system].concept.append(fhir_concept)
    click.echo("\n")
    return fhir_code_systems


def download_from_art_decor(artdecor: str, artdecor_from_file: bool):
    """download the art decor JSON of the ValueSet

    Args:
        artdecor (str): url/path for the JSON value in ArtDecor
        artdecor_from_file (bool): whether the artdecor parameter should be interpreted as an URL (if false) or as a file path (if true)

    Raises:
        ValueError: if the URL is not valid, or invalid data was received from ArtDecor
    """
    if not artdecor_from_file:
        valid_url = validators.url(artdecor)
        if not valid_url:
            raise ValueError(
                f"the value passed for the ArtDecor URL does not seem to be a valid URL. Got {artdecor}.")
        r = requests.get(artdecor)
        j = r.json()
        if j is None:
            raise ValueError("got invalid json from ArtDecor")
        return j
    else:
        with open(artdecor) as f:
            j = json.load(f)
            return j


def validate_attributes_match(existing_cs: CodeSystem, new_cs: CodeSystem):
    attributes = ["id", "url", "valueSet", "version", "title", "status"]
    errors = []
    for attr in attributes:
        existing_attr = existing_cs.dict()[attr]
        new_attr = new_cs.dict()[attr]
        if existing_attr != new_attr:
            errors.append(
                f"mismatch in attribute '{attr}': old '{existing_attr}', new '{new_attr}'")
    return errors


def property_for_concept(
        concept: CodeSystemConcept,
        property_code: str = "parent",
        allow_multiple: bool = False) -> Union[CodeSystemConceptProperty, List[CodeSystemConceptProperty]]:
    if "property" in concept.json():
        props = [p for p in concept.property
                 if p.code == property_code]
        if len(props) == 0:
            return None
        elif len(props) == 1:
            return props[0]
        else:
            if allow_multiple:
                return props
            else:
                raise ValueError(
                    f"multiple properties, but only one expected for concept with code='{concept.code}'")
    else:
        return None


def merge_fhir_json(filepath: str, new_cs: CodeSystem):
    existing_cs = CodeSystem.parse_file(filepath)
    click.echo(f"there is an existing file at {filepath}, merging...")
    validation_errors = validate_attributes_match(existing_cs, new_cs)
    if len(validation_errors) > 0:
        click.echo("there were validation messages when merging:\n  " +
                   ',\n  '.join(validation_errors),
                   err=True, color=True)
        return None
    concept_missing_in_existing = [
        concept for concept in existing_cs.concept
        if concept.code not in [c.code for c in new_cs.concept]
    ]
    if len(concept_missing_in_existing) > 0:
        click.echo("codes missing in the existing CodeSystem: " +
                   ", ".join(f"'{c.code}'='{c.display}'" for c in concept_missing_in_existing))
    concept_missing_in_new = [
        concept for concept in new_cs.concept
        if concept.code not in [c.code for c in existing_cs.concept]
    ]
    if len(concept_missing_in_new) > 0:
        click.echo("codes missing in the new CodeSystem: " +
                   ", ".join(f"'{c.code}'='{c.display}'" for c in concept_missing_in_new))
    concepts_in_both_old = {
        c.code: c for c in existing_cs.concept if c not in concept_missing_in_new}
    concepts_in_both_new = {
        c.code: c for c in new_cs.concept if c not in concept_missing_in_existing}
    merge_errors = []
    for code in concepts_in_both_old.keys():
        assert(code in concepts_in_both_new.keys())
        old_concept: CodeSystemConcept = concepts_in_both_old[code]
        new_concept: CodeSystemConcept = concepts_in_both_new[code]
        if old_concept.display != new_concept.display:
            merge_errors.append(
                f"code '{code}' has different display, old '{old_concept.display}' vs new '{new_concept.display}'")
        old_parent = None
        new_parent = None
        if "property" in old_concept.json():
            old_parent = [p for p in old_concept.property
                          if p.code == "parent"]
        if "property" in new_concept.json():
            new_parent = [p for p in new_concept.property
                          if p.code == "parent"]
        if old_parent != None and new_parent == None or old_parent == None and new_parent != None:
            merge_errors.append(
                f"unhandled parent for code '{code}' in only one code system, please handle.")
        elif old_parent != None and new_parent != None:
            if old_parent.valueCode != new_parent.valueCode:
                merge_errors.append(
                    f"code '{code}' has different parent value, old '{old_parent.valueCode}' vs new '{new_parent.valueCode}'")
    if len(merge_errors) > 0:
        click.echo("there were differences detected in the concepts: \n  " +
                   "\n  ".join(merge_errors), err=True, color=True)
        return None
    existing_cs.concept.extend(concept_missing_in_existing)
    return existing_cs


def write_to_files(ad: Dict, fhir: Dict[str, CodeSystem], output_dir: str):
    for cs_oid, fhir_cs in fhir.items():
        output_filename = path.join(output_dir, f"cs-{fhir_cs.id}.fhir.json")
        if path.exists(output_filename):
            to_write = merge_fhir_json(output_filename, fhir_cs)
        else:
            to_write = fhir_cs
        if to_write is None:
            click.echo("not writing the code system because of errors")
        else:
            click.echo(
                f"writing CodeSystem with OID={cs_oid} to {output_filename}")
            with open(output_filename, "w") as f:
                json.dump(fhir_cs.dict(), f, indent=4,
                          default=json_serial, ensure_ascii=False)
            click.echo("\n")


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code, 
    from https://stackoverflow.com/a/22238613/2333678"""

    if isinstance(obj, (datetime)):
        return obj.date().isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


@ click.command()
@ click.option("--artdecor",
               prompt="URL (per default) or path (if --artdecor-from-file is given) for the JSON file in ArtDecor",
               help="The link to the JSON file in ArtDecor to convert"
               )
@ click.option("--artdecor-from-file",
               is_flag=True)
@ click.option("--output-dir",
               type=click.Path(exists=True, file_okay=False,
                               dir_okay=True, writable=True,
                               resolve_path=True),
               prompt="output directory?")
def cli(artdecor, artdecor_from_file, output_dir):
    json = download_from_art_decor(artdecor, artdecor_from_file)
    converted = convert_to_fhir_codesystems(json)
    write_to_files(json, converted, output_dir)


if __name__ == "__main__":
    cli()
