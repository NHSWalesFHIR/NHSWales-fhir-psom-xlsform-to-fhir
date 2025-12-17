import logging
from typing import List
import pandas as pd
from tqdm import tqdm
import src.string_util as su
from src.models.Fsh_questionnaire import Fsh_questionnaire
from src.models.Fsh_terminology import Fsh_terminology
from src.models.Fsh_question_reference import Fsh_question_reference, Fsh_question_reference_codesystem
from src.models.XLS_Form import XLS_Form
    
def convert_to_fsh(processed_xlsforms: List[XLS_Form]):
    fsh_lines_list_DSCN = []
    fsh_lines_list_LPDS = []
    question_codes_DSCN = []

    for xlsForm in tqdm(processed_xlsforms):
        logging.info(f'Converting {xlsForm.file_name}...')
        questionnaire_fsh_lines = Fsh_questionnaire(xlsForm)            
        questionnaire_terminology_fsh_lines = Fsh_terminology(xlsForm)

        if xlsForm.lpds_healthboard_abbreviation is None:
            # Only collect question references for DSCN questionnaires
            question_reference_fsh = Fsh_question_reference(xlsForm)
            question_codes_DSCN.extend(question_reference_fsh.get_question_codes())
            fsh_lines_list_DSCN.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, []))
        else:
            fsh_lines_list_LPDS.append((xlsForm.file_name, questionnaire_fsh_lines.lines, questionnaire_terminology_fsh_lines.lines, xlsForm.short_name, xlsForm.version, xlsForm.lpds_healthboard_abbreviation, []))

        logging.info(f'Converted {xlsForm.file_name}...')
    
    # Create consolidated QuestionReference CodeSystem for DSCN only
    # LPDS questionnaires do not use item.code elements, so no CodeSystem is needed
    question_reference_codesystem_dscn = Fsh_question_reference_codesystem(question_codes_DSCN, is_lpds=False)
    
    # Add the consolidated CodeSystem to the DSCN list only
    # Note: Version is ignored for QuestionReferenceCS files as they use date-based versioning internally
    fsh_lines_list_DSCN.append(([], [], [], 'QuestionReferenceCS', None, [], question_reference_codesystem_dscn.lines))
    
    return fsh_lines_list_DSCN, fsh_lines_list_LPDS

