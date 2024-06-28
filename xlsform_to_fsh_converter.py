import re, logging
import pandas as pd
from tqdm import tqdm
import string_util as su
from Classes.XlsFormData import XlsFormData
from Classes.Fsh_questionnaire import Fsh_questionnaire
    
def convert_to_fsh(processed_xlsforms):
    fsh_lines_list = []
    ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
    unique_codes = set()
    with tqdm(total=len(processed_xlsforms), desc="Converting to FSH", dynamic_ncols=True) as pbar:
        for file_name, data in processed_xlsforms:
            logging.info(f'Converting {file_name}...')
            questionnaire_fsh_lines = Fsh_questionnaire(data)            
            questionnaire_terminology_fsh_lines = create_fsh_questionnaire_terminology(data)
            ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
            question_reference_codesystem_fsh_lines, code_tuple = create_fsh_question_reference_codesystem(data)
            unique_codes.update(code_tuple)
            pbar.update(1)
            fsh_lines_list.append((file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines, data.short_name, data.version, data.lpds_healthboard_abbreviation, question_reference_codesystem_fsh_lines))
            logging.info(f'Converted {file_name}...')
    
    ## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
    question_reference_valueset_fsh_lines = create_fsh_question_reference_valueset(unique_codes)
    fsh_lines_list.append(([], [], [], 'QuestionReferenceVS', '0.0.1', [], question_reference_valueset_fsh_lines))
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

def create_fsh_questionnaire_terminology(data: XlsFormData) -> list: 
    lines = []
    for list_name in data.df_choices['list_name'].unique():
        proper_list_name = su.convert_to_camel_case(list_name)
       
        if data.lpds_healthboard_abbreviation:
            clean_abbreviation = data.lpds_healthboard_abbreviation.replace('-', '')
            cs_name = (data.lpds_healthboard_abbreviation + data.short_name + proper_list_name + 'CS').replace('-', '_')
            vs_name = (data.lpds_healthboard_abbreviation + data.short_name + proper_list_name + 'VS').replace('-', '_')
            copyright_cs = "The information provided in the CodeSystem may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            copyright_vs = "The information provided in the ValueSet may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = clean_abbreviation

        else:
            cs_name = (data.short_name + proper_list_name + 'CS').replace('-', '_')
            vs_name = (data.short_name + proper_list_name + 'VS').replace('-', '_')
            copyright_cs = "The information provided in the CodeSystem is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            copyright_vs = "The information provided in the ValueSet is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = "NHS Wales"
            
        cs_id = generate_vs_or_cs_id(data.short_name, list_name, 'CS', data.lpds_healthboard_abbreviation)
        vs_id = generate_vs_or_cs_id(data.short_name, list_name, 'VS', data.lpds_healthboard_abbreviation)

        lines_cs = [
            f'CodeSystem: {cs_id}',
            f'Id: {cs_id}',
            f'Title: "{data.short_name} Questionnaire - {proper_list_name} CodeSystem"',
            f'Description: "Codes for the question \'{proper_list_name}\' in PSOM Questionnaire \'{data.title}\'."',
            f'* ^name = "{cs_name}"',
            f'* ^version = "{data.version}"',
            f'* ^status = #draft',
            f'* ^copyright = "{copyright_cs}"',
            f'* ^publisher = "{publisher}"',
            f'* ^caseSensitive = true',
            '',
        ]

        for _, row in data.df_choices[data.df_choices['list_name'] == list_name].iterrows():
            code = f'* #{row["name"]} "{su.escape_quotes(row["label"])}"'
            lines_cs.append(code)
        
        lines.extend(lines_cs)
        lines.append('')

        lines_vs = [
            f'ValueSet: {vs_id}',
            f'Id: {vs_id}',
            f'Title: "{data.short_name} Questionnaire - {proper_list_name} ValueSet"',
            f'Description: "Applicable codes for the question \'{proper_list_name}\' in PSOM Questionnaire \'{data.title}\'."',
            f'* ^name = "{vs_name}"',
            f'* ^version = "{data.version}"',
            f'* ^status = #draft',
            f'* ^copyright = "{copyright_vs}"',
            f'* ^publisher = "{publisher}"',
            '',
        ]
    
        for _, row in data.df_choices[data.df_choices['list_name'] == list_name].iterrows():
            code = f'* {cs_id}#{row["name"]} "{su.escape_quotes(row["label"])}"'
            lines_vs.append(code)
        
        lines.extend(lines_vs)
        lines.append('')

    return lines

# AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
def create_fsh_question_reference_codesystem(data: XlsFormData) -> list:
   lines = []
   if data.lpds_healthboard_abbreviation:
       cs_name = (data.lpds_healthboard_abbreviation + data.short_name + 'QuestionReferenceCS').replace('-', '_')
       cs_id = su.make_fhir_compliant((data.lpds_healthboard_abbreviation + '-' + data.short_name + '-' + 'QuestionReferenceCS'))
       copyright = "TO ADD"
   else:
       cs_name = (data.short_name + 'QuestionReferenceCS').replace('-', '_')
       cs_id = su.make_fhir_compliant((data.short_name + '-' + 'QuestionReferenceCS'))
       copyright = "The information provided in this CodeSystem must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."

   lines_cs = [
       f'CodeSystem: {cs_id}',
       f'Id: {cs_id}',
       f'Title: "{data.short_name} Question Reference CodeSystem"',
       f'Description: "Question Reference codes for the questions in PSOM Questionnaire \'{data.title}\'."',
       f'* ^name = "{cs_name}"',
       f'* ^version = "{data.version}"',
       f'* ^status = #draft',
       f'* ^copyright = "{copyright}"',
       f'* ^publisher = "{data.lpds_healthboard_abbreviation or "NHS Wales"}"',
       f'* ^caseSensitive = true',
       '',
   ]
   seen = set()  # Set to keep track of seen (name, label) pairs

   for _, row in data.df_survey.iterrows():
       if pd.notna(row["name"]) and row["name"] != '':  # Check for non-empty "name"
           code_tuple = (row["name"], row["label"], cs_id)
           if code_tuple not in seen:
               code = f'* #{row["name"]} "{su.escape_quotes(row["label"])}"'
               lines_cs.append(code)
               seen.add(code_tuple)
    
   lines.extend(lines_cs)
   lines.append('')

   return lines, seen
## AT 15/11/2023: decided in Oct to (temporary) not use this feature until a proper use case for it has been identified. 
def create_fsh_question_reference_valueset(unique_codes) -> list:
    lines = [
        f'ValueSet: QuestionReferenceVS',
        f'Id: QuestionReferenceVS',
        f'Title: "Question Reference ValueSet"',
        f'Description: "Accumulated question reference codes for the questions in PSOM Questionnaires."',
        f'* ^name = "DataStandardsWalesPROMSQuestionReferenceVS"',
        f'* ^status = #draft',
        f'* ^copyright = "The information provided in this ValueSet must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."',
        f'* ^publisher = "NHS Wales"',
        '',
        ] 
    # Sort unique_codes by the 'name' field
    sorted_unique_codes = sorted(unique_codes, key=lambda x: x[0])

    for name, label, cs_id in sorted_unique_codes:
        code = f'* {cs_id}#{name} "{su.escape_quotes(label)}"'
        lines.append(code)

    lines.append('')

    return lines