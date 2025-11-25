import pandas as pd
import string_util as su
from datetime import datetime
from Classes.XLS_Form import XLS_Form
from constants import (
    QUESTION_REFERENCE_CS_URL_DSCN,
    QUESTION_REFERENCE_CS_URL_LPDS,
    NHS_WALES_PUBLISHER,
    COPYRIGHT_QUESTION_REFERENCE_DSCN,
    FHIR_STATUS_DRAFT
)

class Fsh_question_reference:

    def __init__(self, data: XLS_Form):
        """
        FSH representation of question reference codes. Extracts question codes from an XLSForm 
        for inclusion in a consolidated QuestionReference CodeSystem.

        Args:
            data (XLS_Form): The data from an XLSForm.
        """

        self.data = data
        self.question_codes = []  # Track question codes from this form

        # Extract question codes from survey
        self._extract_question_codes()

    def _extract_question_codes(self):
        """Extract question codes from the survey data."""
        for _, row in self.data.df_survey.iterrows():
            if pd.notna(row["name"]) and row["name"] != '':  # Check for non-empty "name"
                code_tuple = (row["name"], su.escape_quotes(row["label"]))
                if code_tuple not in self.question_codes:
                    self.question_codes.append(code_tuple)

    def get_question_codes(self):
        """Return the list of question codes from this form."""
        return self.question_codes

class Fsh_question_reference_codesystem:

    def __init__(self, all_question_codes: list, is_lpds: bool = False):
        """
        FSH representation of consolidated question reference CodeSystem.

        Args:
            all_question_codes (list): List of all unique question codes from multiple XLS forms.
            is_lpds (bool): Whether this is for LPDS or DSCN forms.
        """

        self.all_question_codes = all_question_codes
        self.is_lpds = is_lpds
        self.lines = []

        self._generate_question_reference_codesystem()

    def _generate_question_reference_codesystem(self):
        """Generate the consolidated QuestionReference CodeSystem."""
        
        if self.is_lpds:
            cs_name = "LPDSQuestionReferenceCS"
            cs_id = "LPDSQuestionReferenceCS"
            cs_url = QUESTION_REFERENCE_CS_URL_LPDS
            title = "LPDS Question Reference CodeSystem"
            description = "Question Reference codes for the questions in LPDS PROM Questionnaires."
            publisher = NHS_WALES_PUBLISHER
            # No copyright for LPDS forms
            copyright_line = []
        else:
            cs_name = "DataStandardsWalesQuestionReferenceCS"
            cs_id = "QuestionReferenceCS"
            cs_url = QUESTION_REFERENCE_CS_URL_DSCN
            title = "Question Reference CodeSystem"
            description = "Question Reference codes for the questions in PSOM Questionnaires."
            publisher = NHS_WALES_PUBLISHER
            # Include copyright for DSCN forms
            copyright = COPYRIGHT_QUESTION_REFERENCE_DSCN
            copyright_line = [f'* ^copyright = "{copyright}"']

        # Generate current date in YYYYMMDD format
        current_date = datetime.now().strftime("%Y%m%d")

        # Build the header
        header_lines = [
            f'CodeSystem: {cs_id}',
            f'Id: {cs_id}',
            f'Title: "{title}"',
            f'Description: "{description}"',
            f'* ^url = "{cs_url}"',
            f'* ^name = "{cs_name}"',
            f'* ^version = "{current_date}"',
            f'* ^status = {FHIR_STATUS_DRAFT}',
        ]

        # Add copyright line if it exists
        if copyright_line:
            header_lines.extend(copyright_line)

        header_lines.extend([
            f'* ^publisher = "{publisher}"',
            f'* ^caseSensitive = true',
            ''
        ])

        self.lines.extend(header_lines)

        # Add all unique codes (deduplicate by code only, keep first occurrence's display text)
        # Skip group entries that end with "_group" or contain "group"
        seen_codes = set()
        for code, display in self.all_question_codes:
            if not (code.endswith('_group') or 'group' in code.lower()):
                if code not in seen_codes:
                    code_line = f'* #{code} "{display}"'
                    self.lines.append(code_line)
                    seen_codes.add(code)

        self.lines.append('')