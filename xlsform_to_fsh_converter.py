import logging
from typing import List
import pandas as pd
from tqdm import tqdm
import string_util as su
from Classes.Fsh_questionnaire import Fsh_questionnaire
from Classes.Fsh_terminology import Fsh_terminology
from Classes.XLS_Form import XLS_Form
    
def convert_to_fsh(processed_xlsforms: List[XLS_Form]):
    fsh_lines_list_DSCN = []
    fsh_lines_list_LPDS = []
    unique_codes_DSCN = []
    unique_codes_LPDS = []

    for xlsForm in tqdm(processed_xlsforms):
        logging.info(f'Converting {xlsForm.file_name}...')
        questionnaire_fsh_lines = Fsh_questionnaire(xlsForm)            
        questionnaire_terminology_fsh_lines = Fsh_terminology(xlsForm)
        question_reference_codesystem_fsh_lines, code_tuple = create_fsh_question_reference_codesystem(xlsForm)

        if xlsForm.lpds_healthboard_abbreviation is None:
            unique_codes_DSCN.append(code_tuple)
            fsh_lines_list_DSCN.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, question_reference_codesystem_fsh_lines))
        else:
            unique_codes_LPDS.append(code_tuple)
            fsh_lines_list_LPDS.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, question_reference_codesystem_fsh_lines))

        logging.info(f'Converted {xlsForm.file_name}...')
    
    question_reference_valueset_fsh_lines_DSCN = create_fsh_question_reference_valueset(unique_codes_DSCN)
    question_reference_valueset_fsh_lines_LPDS = create_fsh_question_reference_valueset(unique_codes_LPDS)
    fsh_lines_list_DSCN.append(([], [], [], 'QuestionReferenceVSDSCN', '0.0.1', [], question_reference_valueset_fsh_lines_DSCN))
    fsh_lines_list_LPDS.append(([], [], [], 'QuestionReferenceVSLPDS', '0.0.1', 'LPDS', question_reference_valueset_fsh_lines_LPDS))
    return fsh_lines_list_DSCN, fsh_lines_list_LPDS


def create_fsh_question_reference_codesystem(data: XLS_Form) -> list:
   lines = []
   if data.lpds_healthboard_abbreviation:
       cs_name = (data.lpds_healthboard_abbreviation + data.short_name + 'QuestionReferenceCS').replace('-', '_')
       cs_id = su.make_fhir_compliant((data.lpds_healthboard_abbreviation + '-' + data.short_name + '-' + 'QuestionReferenceCS'))
       #copyright = "TO ADD"
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
   seen = [] # Set to keep track of seen (name, label) pairs

   for _, row in data.df_survey.iterrows():
       if pd.notna(row["name"]) and row["name"] != '':  # Check for non-empty "name"
           code_tuple = (row["name"], row["label"], cs_id)
           if code_tuple not in seen:
               code = f'* #{row["name"]} "{su.escape_quotes(row["label"])}"'
               lines_cs.append(code)
               seen.append(code_tuple)
    
   lines.extend(lines_cs)
   lines.append('')

   return lines, seen

def create_fsh_question_reference_valueset(unique_codes: list) -> list:
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

    for codesystem in unique_codes:
        for name, label, cs_id in codesystem:
            code = f'* {cs_id}#{name} "{su.escape_quotes(label)}"'
            lines.append(code)

    lines.append('')

    return lines