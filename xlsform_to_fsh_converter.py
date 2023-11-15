import re, logging
import pandas as pd
from tqdm import tqdm
import string_util as su
    
def convert_to_fsh(processed_xlsforms):
    fsh_lines_list = []
    ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
    #unique_codes = set()
    with tqdm(total=len(processed_xlsforms), desc="Converting to FSH", dynamic_ncols=True) as pbar:
        for file_name, df_survey, df_choices, short_name, short_id, version, title, lpds_healthboard_abbreviation in processed_xlsforms:
                logging.info(f'Converting {file_name}...')
                questionnaire_fsh_lines = create_fsh_questionnaire(df_survey, short_name, short_id, version, title, lpds_healthboard_abbreviation)            
                questionnaire_terminology_fsh_lines = create_fsh_questionnaire_terminology(df_choices, short_name, short_id, version, title, lpds_healthboard_abbreviation)
                ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
                # question_reference_codesystem_fsh_lines, code_tuple = create_fsh_question_reference_codesystem(df_survey, short_name, short_id, version, title, lpds_healthboard_abbreviation)
                # unique_codes.update(code_tuple)
                # pbar.update(1)
                # fsh_lines_list.append((file_name, questionnaire_fsh_lines, questionnaire_terminology_fsh_lines, question_reference_codesystem_fsh_lines,[], short_name, version))
                pbar.update(1)
                fsh_lines_list.append((file_name, questionnaire_fsh_lines, questionnaire_terminology_fsh_lines, short_name, version, lpds_healthboard_abbreviation))
                logging.info(f'Converted {file_name}...')
    
    ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
    #question_reference_valueset_fsh_lines = create_fsh_question_reference_valueset(unique_codes)
    #fsh_lines_list.append(("QuestionReferenceVS", [], [],[], question_reference_valueset_fsh_lines, 'QuestionReferenceVS', '0.0.1'))

    return fsh_lines_list

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


def create_fsh_questionnaire(df_survey: pd.DataFrame, short_name: str, short_id: str, version: str, title: str, lpds_healthboard_abbreviation: str = None) -> list:   
    questionnaire_name = short_name.replace('-', '_')
    # pattern to select 'select  one' and 'select one' and 'selecte one ' 
    select_one_pattern = re.compile("select[_ ]one[_ ]?", re.IGNORECASE)

    if lpds_healthboard_abbreviation:
        instance_id = f'{lpds_healthboard_abbreviation}-{short_name}'
        name = f'{lpds_healthboard_abbreviation}{questionnaire_name}'
        copyright = "The information provided in this Questionnaire may not be used to re-produce a PROM questionnaire form, this may result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
    else:
        instance_id = f'DataStandardsWales-PSOM-{short_name}'
        name = f'DataStandardsWalesPSOM{questionnaire_name}'
        copyright = "© 2023 NHS Wales. The information provided in this Questionnaire must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used." 

    lines = [
        f'Instance: {instance_id}',
        'InstanceOf: Questionnaire',
        'Usage: #definition',
        f'* title = "{title}"',
        f'* name = "{name}"',
        f'* version = "{version}"',
        f'* status = #draft',
        f'* description = "PSOM Questionnaire: {title}."',
        f'* copyright = "{copyright}"',
        '',
        ]

    indent_level = 0
    for _, row in df_survey.iterrows():
        indent = '  ' * indent_level
        extension_added = False  # Initialize as False for each new row
        
        if pd.isna(row["format"]) and \
            (row['type'] in ['text', 'decimal', 'integer'] or select_one_pattern.match(row['type'])):
            logging.warning(f"Warning processing {short_name}: found no format for {row['name']}. ")

        if row['type'] in ['text', 'decimal', 'integer', 'begin group', 'begin_group'] or select_one_pattern.match(row['type']):
            lines.append(f'{indent}* item[+]')
        
        if  row['sensitive'] in ['1', 'true', 'y', 'yes'] or row['sensitive'] == 1 :
            if not extension_added:  # If no extension has been added yet
                lines.append(f'{indent}  * extension[0].url = "http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label"')
                extension_added = True  # Set to True because an extension has been added
            else:
                lines.append(f'{indent}  * extension[+].url = "http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label"')
            lines.append(f'{indent}  * extension[=].valueCoding = http://terminology.hl7.org/CodeSystem/v3-ActCode#PDS "patient default information sensitivity"')

        if row['type'] == 'begin group' or row['type'] == 'begin_group':
            lines.append(f'{indent}  * linkId = "{row["name"]}"')
            lines.append(f'{indent}  * text = "{su.escape_quotes(row["label"])}"')
            lines.append(f'{indent}  * type = #group')
            indent_level += 1
            lines.append('')

        elif select_one_pattern.match(row['type']):
            # Use regex sub to replace all occurrences of 'select_one ' or 'select one ' with empty string, and remove extra whitespaces
            ValueSetName  = select_one_pattern.sub('', row["type"])
            ValueSetId = generate_vs_or_cs_id(short_name, ValueSetName, 'VS', lpds_healthboard_abbreviation)

            if not extension_added:  
                lines.append(f'{indent}  * extension[0].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
                extension_added = True  
            else:
                lines.append(f'{indent}  * extension[+].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
            lines.append(f'{indent}  * extension[=].valueString = "{row["format"]}"')
            lines.append(f'{indent}  * linkId = "{row["name"]}"')
            lines.append(f'{indent}  * text = "{su.escape_quotes(row["label"])}"')
            lines.append(f'{indent}  * type = #choice')
            lines.append(f'{indent}  * answerValueSet = Canonical({ValueSetId})')
            lines.append('')

        elif row['type'] == 'text':
            if not extension_added:  
                lines.append(f'{indent}  * extension[0].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
                extension_added = True  
            else:
                lines.append(f'{indent}  * extension[+].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
            lines.append(f'{indent}  * extension[=].valueString = "{row["format"]}"')
            lines.append(f'{indent}  * linkId = "{row["name"]}"')
            lines.append(f'{indent}  * text = "{su.escape_quotes(row["label"])}"')
            lines.append(f'{indent}  * type = #string')
            lines.append('')

        elif row['type'] in ['decimal', 'integer']:
            if not extension_added:  
                lines.append(f'{indent}  * extension[0].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
                extension_added = True  
            else:
                lines.append(f'{indent}  * extension[+].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
            lines.append(f'{indent}  * extension[=].valueString = "{row["format"]}"')
            lines.append(f'{indent}  * linkId = "{row["name"]}"')
            lines.append(f'{indent}  * text = "{su.escape_quotes(row["label"])}"')
            lines.append(f'{indent}  * type = #{row["type"]}')
            lines.append('')

        elif row['type'] == 'end group' or row['type'] == 'end_group':
            indent_level -= 1

        else:
            print('Encountered not supported type found in' + short_name + '   ' + row['name'] )
            logging.error(f"Error processing {short_name}: found unsupported datatype for {row['name']}. {row['type']} is not supported (yet). ")

    return lines

def create_fsh_questionnaire_terminology(df_choices: pd.DataFrame, short_name: str, short_id: str, version: str, title: str, lpds_healthboard_abbreviation: str = None) -> list: 
    lines = []
    for list_name in df_choices['list_name'].unique():
        proper_list_name = su.convert_to_camel_case(list_name)
       
        if lpds_healthboard_abbreviation:
            clean_abbreviation = lpds_healthboard_abbreviation.replace('-', '')
            prefix = lpds_healthboard_abbreviation + '-'
            cs_name = (lpds_healthboard_abbreviation + short_name + proper_list_name + 'CS').replace('-', '_')
            vs_name = (lpds_healthboard_abbreviation + short_name + proper_list_name + 'VS').replace('-', '_')
            copyright_cs = "The information provided in the CodeSystem may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            copyright_vs = "The information provided in the ValueSet may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = clean_abbreviation

        else:
            prefix = ''
            cs_name = (short_name + proper_list_name + 'CS').replace('-', '_')
            vs_name = (short_name + proper_list_name + 'VS').replace('-', '_')
            copyright_cs = "© 2023 NHS Wales. The information provided in the CodeSystem is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            copyright_vs = "© 2023 NHS Wales. The information provided in the ValueSet is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = "NHS Wales"
            
        cs_id = generate_vs_or_cs_id(short_name, list_name, 'CS', lpds_healthboard_abbreviation)
        vs_id = generate_vs_or_cs_id(short_name, list_name, 'VS', lpds_healthboard_abbreviation)

        lines_cs = [
            f'CodeSystem: {cs_id}',
            f'Id: {cs_id}',
            f'Title: "{short_name} Questionnaire - {proper_list_name} CodeSystem"',
            f'Description: "Codes for the question \'{proper_list_name}\' in PSOM Questionnaire \'{title}\'."',
            f'* ^name = "{cs_name}"',
            f'* ^version = "{version}"',
            f'* ^status = #draft',
            f'* ^copyright = "{copyright_cs}"',
            f'* ^publisher = "{publisher}"',
            f'* ^caseSensitive = true',
            '',
        ]

        for _, row in df_choices[df_choices['list_name'] == list_name].iterrows():
            code = f'* #{row["name"]} "{su.escape_quotes(row["label"])}"'
            lines_cs.append(code)
        
        lines.extend(lines_cs)
        lines.append('')

        lines_vs = [
            f'ValueSet: {vs_id}',
            f'Id: {vs_id}',
            f'Title: "{short_name} Questionnaire - {proper_list_name} ValueSet"',
            f'Description: "Applicable codes for the question \'{proper_list_name}\' in PSOM Questionnaire \'{title}\'."',
            f'* ^name = "{vs_name}"',
            f'* ^version = "{version}"',
            f'* ^status = #draft',
            f'* ^copyright = "{copyright_vs}"',
            f'* ^publisher = "{prefix or "NHS Wales"}"',
            '',
        ]
    
        for _, row in df_choices[df_choices['list_name'] == list_name].iterrows():
            code = f'* {cs_id}#{row["name"]} "{su.escape_quotes(row["label"])}"'
            lines_vs.append(code)
        
        lines.extend(lines_vs)
        lines.append('')

    return lines

## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
#def create_fsh_question_reference_codesystem(df_survey: pd.DataFrame, short_name: str, short_id: str, version: str, title: str, lpds_healthboard_abbreviation: str = None) -> list:
#    lines = []
#    if lpds_healthboard_abbreviation:
#        cs_name = (lpds_healthboard_abbreviation + short_name + 'QuestionReferenceCS').replace('-', '_')
#        cs_id = su.make_fhir_compliant((lpds_healthboard_abbreviation + '-' + short_name + '-' + 'QuestionReferenceCS'))
#        copyright = "TO ADD"
#    else:
#        cs_name = (short_name + 'QuestionReferenceCS').replace('-', '_')
#        cs_id = su.make_fhir_compliant((short_name + '-' + 'QuestionReferenceCS'))
#        copyright = "© 2023 NHS Wales. The information provided in this CodeSystem must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
#
#    lines_cs = [
#        f'CodeSystem: {cs_id}',
#        f'Id: {cs_id}',
#        f'Title: "{short_name} Question Reference CodeSystem"',
#        f'Description: "Question Reference codes for the questions in PSOM Questionnaire \'{title}\'."',
#        f'* ^name = "{cs_name}"',
#        f'* ^version = "{version}"',
#        f'* ^status = #draft',
#        f'* ^copyright = "{copyright}"',
#        f'* ^publisher = "{lpds_healthboard_abbreviation or "NHS Wales"}"',
#        f'* ^caseSensitive = true',
#        '',
#    ]
#    seen = set()  # Set to keep track of seen (name, label) pairs
#
#    for _, row in df_survey.iterrows():
#        if pd.notna(row["name"]):  # Check for non-empty "name"
#            code_tuple = (row["name"], row["label"], cs_id)
#            if code_tuple not in seen:
#                code = f'* #{row["name"]} "{su.escape_quotes(row["label"])}"'
#                lines_cs.append(code)
#                seen.add(code_tuple)
#    
#    lines.extend(lines_cs)
#    lines.append('')
#
#    return lines, seen

## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
#def create_fsh_question_reference_valueset(unique_codes) -> list:
#    lines = [
#            f'ValueSet: QuestionReferenceVS',
#            f'Id: QuestionReferenceVS',
#            f'Title: "Question Reference ValueSet"',
#            f'Description: "Accumulated question reference codes for the questions in PSOM Questionnaires."',
#            f'* ^name = "DataStandardsWalesPROMSQuestionReferenceVS"',
#            f'* ^status = #draft',
#            f'* ^copyright = "© 2023 NHS Wales. The information provided in this ValueSet must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."',
#            f'* ^publisher = "NHS Wales"',
#            '',
#            ] 
#    # Sort unique_codes by the 'name' field
#    sorted_unique_codes = sorted(unique_codes, key=lambda x: x[0])
#
#    for name, label, cs_id in sorted_unique_codes:
#        code = f'* {cs_id}#{name} "{su.escape_quotes(label)}"'
#        lines.append(code)
#
#    lines.append('')
#
#    return lines
