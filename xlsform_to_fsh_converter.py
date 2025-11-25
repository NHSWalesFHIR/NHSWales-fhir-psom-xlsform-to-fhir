import logging
from typing import List
import pandas as pd
from tqdm import tqdm
import string_util as su
from Classes.Fsh_questionnaire import Fsh_questionnaire
from Classes.Fsh_terminology import Fsh_terminology
from Classes.Fsh_question_reference import Fsh_question_reference, Fsh_question_reference_codesystem
from Classes.XLS_Form import XLS_Form
    
def convert_to_fsh(processed_xlsforms: List[XLS_Form]):
    fsh_lines_list_DSCN = []
    fsh_lines_list_LPDS = []
    question_codes_DSCN = []
    question_codes_LPDS = []

    for xlsForm in tqdm(processed_xlsforms):
        logging.info(f'Converting {xlsForm.file_name}...')
        questionnaire_fsh_lines = Fsh_questionnaire(xlsForm)            
        questionnaire_terminology_fsh_lines = Fsh_terminology(xlsForm)
        question_reference_fsh = Fsh_question_reference(xlsForm)

        if xlsForm.lpds_healthboard_abbreviation is None:
            question_codes_DSCN.extend(question_reference_fsh.get_question_codes())
            fsh_lines_list_DSCN.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, []))
        else:
            question_codes_LPDS.extend(question_reference_fsh.get_question_codes())
            fsh_lines_list_LPDS.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, []))

        logging.info(f'Converted {xlsForm.file_name}...')
    
    # Create consolidated QuestionReference CodeSystems
    question_reference_codesystem_dscn = Fsh_question_reference_codesystem(question_codes_DSCN, is_lpds=False)
    question_reference_codesystem_lpds = Fsh_question_reference_codesystem(question_codes_LPDS, is_lpds=True)
    
    # Add the consolidated CodeSystems to the lists
    fsh_lines_list_DSCN.append(([], [], [], 'QuestionReferenceCS', '0.0.1', [], question_reference_codesystem_dscn.lines))
    fsh_lines_list_LPDS.append(([], [], [], 'QuestionReferenceCS', '0.0.1', 'LPDS', question_reference_codesystem_lpds.lines))
    
    return fsh_lines_list_DSCN, fsh_lines_list_LPDS

