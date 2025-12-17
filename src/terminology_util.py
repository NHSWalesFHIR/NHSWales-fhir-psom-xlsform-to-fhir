import src.string_util as su

def generate_vs_or_cs_id(short_name: str, list_name: str, id_type: str, lpds_healthboard_abbreviation: str = None) -> str:
    """
    Generate a FHIR compliant ID for CodeSystem or ValueSet.

    Args:
        short_name (str): The short name of the questionnaire.
        list_name (str): The name of the list in the questionnaire.
        id_type (str): The type of ID to generate ('CS' for CodeSystem, 'VS' for ValueSet).
        lpds_healthboard_abbreviation (str, optional): The LPDS healthboard abbreviation. Defaults to None.

    Returns:
        str: The FHIR compliant ID.
    """
    proper_list_name = su.convert_to_camel_case(list_name)
    prefix = lpds_healthboard_abbreviation + '-' if lpds_healthboard_abbreviation else ''
    vs_or_cs_id = su.make_fhir_compliant(prefix + short_name + '-' + proper_list_name + id_type)
    return vs_or_cs_id