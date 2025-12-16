import re, logging
from Classes.XLS_Form import XLS_Form
import string_util as su
import pandas as pd
import terminology_util as tu
from constants import (
    QUESTION_REFERENCE_CS_URL_DSCN,
    QUESTION_REFERENCE_CS_URL_LPDS,
    NHS_WALES_PUBLISHER,
    COPYRIGHT_QUESTIONNAIRE_LPDS,
    COPYRIGHT_QUESTIONNAIRE_DSCN,
    ENTRY_FORMAT_EXTENSION_URL,
    SECURITY_LABEL_EXTENSION_URL,
    FHIR_STATUS_DRAFT
)

class Fsh_questionnaire:

    def __init__(self, data: XLS_Form):
        """
        FSH representation of a questionnaire. Transforms a XLSForm into a FSH questionnaire.

        Args:
            data (XlsFormData): The data from an XLSForm.
        """
        
        self.data = data

        # Check if 'sensitive' column exists in the survey sheet and warn if missing
        if 'sensitive' not in data.df_survey.columns:
            logging.warning(f"{data.file_name}: 'sensitive' column not found in survey sheet. Questions will not be marked as sensitive/confidential. Add a 'sensitive' column with values like 'true', '1', 'yes' to mark sensitive questions.")

        questionnaire_name = data.short_name.replace('-', '_')
        
        # Robust patterns for XLSForm field types with comprehensive matching
        # Handles variations in spacing, underscores, and common typos
        self.select_one_pattern = re.compile(r"select[_\s]*one[_\s]*", re.IGNORECASE)
        self.select_multiple_pattern = re.compile(r"select[_\s]*multiple[_\s]*", re.IGNORECASE)
        
        # Additional patterns for other XLSForm types that might be encountered
        self.group_patterns = {
            'begin_group': re.compile(r"begin[_\s]*group", re.IGNORECASE),
            'end_group': re.compile(r"end[_\s]*group", re.IGNORECASE)
        }
        
        # Validation patterns for known field types in XLSForm spec
        self.known_types = {
            'text', 'decimal', 'integer', 'note', 'calculate', 'hidden',
            'date', 'time', 'datetime', 'geopoint', 'geotrace', 'geoshape',
            'barcode', 'acknowledge', 'image', 'audio', 'video', 'file'
        }

        if data.lpds_healthboard_abbreviation:
            clean_abbreviation = data.lpds_healthboard_abbreviation.replace('-', '')
            instance_id = f'{data.lpds_healthboard_abbreviation}-{data.short_name}'
            name = f'LPDS{data.lpds_healthboard_abbreviation}{questionnaire_name}'
            copyright = "The information provided in this Questionnaire may not be used to re-produce a PROM questionnaire form, this may result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = clean_abbreviation

        else:
            instance_id = f'DataStandardsWales-PSOM-{data.short_name}'
            name = f'DataStandardsWalesPSOM{questionnaire_name}'
            copyright = COPYRIGHT_QUESTIONNAIRE_DSCN
            publisher = NHS_WALES_PUBLISHER

        self.lines = [
            f'Instance: {instance_id}',
            'InstanceOf: Questionnaire',
            'Usage: #definition',
            f'* title = "{data.title}"',
            f'* name = "{name}"',
            f'* version = "{data.version}"',
            f'* status = {FHIR_STATUS_DRAFT}',
            f'* publisher = "{publisher}"',
            f'* description = "PSOM Questionnaire: {data.title}."',
            f'* copyright = "{copyright}"',
            '',
            ]
        
        self.indent_level = 0
        for _, row in data.df_survey.iterrows():
            self.indent = '  ' * self.indent_level
            self.extension_added = False

            # Determine field type using improved pattern matching
            field_type = self._classify_field_type(row['type'])
            
            # Check for missing format values for field types that need them
            # Note: keep_default_na=False in XLS_Form.py means empty cells are '' not NaN
            format_value = row["format"]
            if (pd.isna(format_value) or (isinstance(format_value, str) and format_value.strip() == '')) and field_type in ['text', 'decimal', 'integer', 'select_one', 'select_multiple']:
                warning_msg = f"processing {data.short_name}: found no format for '{row['name']}'. entryFormat extension will be omitted from FHIR output."
                logging.warning(warning_msg)
            
            if field_type in ['text', 'decimal', 'integer', 'select_one', 'select_multiple', 'note', 'begin_group']:
                self.lines.append(f'{self.indent}* item[+]')

            # Check if 'sensitive' column exists and has a truthy value
            if 'sensitive' in row and self._is_sensitive_field(row['sensitive']):
                self._add_security_extension()

            # Handle different field types using the classified type
            if field_type == 'begin_group':
                self.handle_group(row)
            elif field_type == 'text':
                self.handle_question(row, 'string')
            elif field_type in ['decimal', 'integer']:
                self.handle_question(row, field_type)
            elif field_type == 'note':
                self.handle_question(row, 'display')
            elif field_type == 'select_one':
                self.handle_question(row, 'choice', True)
            elif field_type == 'select_multiple':
                # Enhanced warning for select_multiple usage
                warning_msg = (
                    f"select_multiple field type detected for '{row['name']}' in {data.short_name}. "
                    f"This feature is EXPERIMENTAL and added for future support only. "
                )
                logging.warning(warning_msg)
                self.handle_question(row, 'choice', True, True)  # True for repeats
            elif field_type == 'end_group':
                self.indent_level -= 1
            else:
                # Enhanced error reporting with suggestions
                error_msg = f"Unsupported field type '{row['type']}' for field '{row['name']}' in {data.short_name}"
                suggestion = self._suggest_type_correction(row['type'])
                if suggestion:
                    error_msg += f". Did you mean '{suggestion}'?"
                
                print(f'Encountered unsupported type: {error_msg}')
                logging.error(f"processing {data.short_name}: {error_msg}")

    def handle_group(self, row: pd.Series):
        self.lines.append(f'{self.indent}  * linkId = "{row["name"]}"')
        
        # Check if label is empty and warn, omit text field if empty
        label_value = row["label"]
        if pd.isna(label_value) or (isinstance(label_value, str) and label_value.strip() == ''):
            warning_msg = f"Warning processing {self.data.short_name}: group '{row['name']}' has no label. The 'text' element will be omitted from FHIR output."
            logging.warning(warning_msg)
        else:
            self.lines.append(f'{self.indent}  * text = "{su.escape_quotes(row["label"])}"')
        
        self.lines.append(f'{self.indent}  * type = #group')
        self.indent_level += 1
        self.lines.append('')

    def handle_question(self, row : pd.Series, type: str, answerValueset: bool = False, repeats: bool = False):
        # Only add entryFormat extension if format value is provided and not empty
        if not pd.isna(row["format"]) and str(row["format"]).strip():
            if not self.extension_added:  
                self.lines.append(f'{self.indent}  * extension[0].url = "{ENTRY_FORMAT_EXTENSION_URL}"')
                self.extension_added = True  
            else:
                self.lines.append(f'{self.indent}  * extension[+].url = "{ENTRY_FORMAT_EXTENSION_URL}"')
            self.lines.append(f'{self.indent}  * extension[=].valueString = "{row["format"]}"')
        
        self.lines.append(f'{self.indent}  * linkId = "{row["name"]}"')
        # Only add item.code for DSCN questionnaires, not for LPDS
        # Also exclude display items (notes) as they are not actual questions
        if not self.data.lpds_healthboard_abbreviation and type != 'display':
            self.lines.append(f'{self.indent}  * code = {QUESTION_REFERENCE_CS_URL_DSCN}#{row["name"]}')
        
        # Check if label is empty and warn, omit text field if empty
        label_value = row["label"]
        if pd.isna(label_value) or (isinstance(label_value, str) and label_value.strip() == ''):
            warning_msg = f"Warning processing {self.data.short_name}: question '{row['name']}' has no label. The 'text' element will be omitted from FHIR output."
            logging.warning(warning_msg)
        else:
            self.lines.append(f'{self.indent}  * text = "{su.escape_quotes(row["label"])}"')
        
        self.lines.append(f'{self.indent}  * type = #{type}')
        
        if repeats:
            self.lines.append(f'{self.indent}  * repeats = true')

        if answerValueset:
            # Handle both select_one and select_multiple patterns
            if self.select_one_pattern.match(row["type"]):
                ValueSetName = self.select_one_pattern.sub('', row["type"])
            elif self.select_multiple_pattern.match(row["type"]):
                ValueSetName = self.select_multiple_pattern.sub('', row["type"])
            else:
                ValueSetName = row["type"]  # fallback
            
            ValueSetId = tu.generate_vs_or_cs_id(self.data.short_name, ValueSetName, 'VS', self.data.lpds_healthboard_abbreviation)
            self.lines.append(f'{self.indent}  * answerValueSet = Canonical({ValueSetId})')

        self.lines.append('')

    def _classify_field_type(self, field_type: str) -> str:
        """
        Classify XLSForm field types using robust pattern matching.
        
        Args:
            field_type (str): The raw field type from XLSForm
            
        Returns:
            str: Standardized field type or 'unknown'
        """
        if not field_type or pd.isna(field_type):
            return 'unknown'
        
        field_type = str(field_type).strip()
        
        # Check for exact matches first
        if field_type.lower() in self.known_types:
            return field_type.lower()
        
        # Check group patterns
        if self.group_patterns['begin_group'].match(field_type):
            return 'begin_group'
        if self.group_patterns['end_group'].match(field_type):
            return 'end_group'
            
        # Check select patterns
        if self.select_one_pattern.match(field_type):
            return 'select_one'
        if self.select_multiple_pattern.match(field_type):
            return 'select_multiple'
            
        return 'unknown'

    def _is_sensitive_field(self, sensitive_value) -> bool:
        """
        Check if a field should be marked as sensitive/confidential.
        
        Args:
            sensitive_value: Value from the 'sensitive' column
            
        Returns:
            bool: True if the field should be marked as sensitive
        """
        if pd.isna(sensitive_value):
            return False
        
        # Convert to string and check various truthy values
        str_value = str(sensitive_value).lower().strip()
        return str_value in ['1', 'true', 'y', 'yes', 't'] or sensitive_value == 1

    def _add_security_extension(self):
        """Add security labeling extension for sensitive fields."""
        if not self.extension_added:
            self.lines.append(f'{self.indent}  * extension[0].url = "{SECURITY_LABEL_EXTENSION_URL}"')
            self.extension_added = True
        else:
            self.lines.append(f'{self.indent}  * extension[+].url = "{SECURITY_LABEL_EXTENSION_URL}"')
        self.lines.append(f'{self.indent}  * extension[=].valueCoding = http://terminology.hl7.org/CodeSystem/v3-ActCode#PDS "patient default information sensitivity"')

    def _suggest_type_correction(self, field_type: str) -> str:
        """
        Suggest a correction for unsupported field types based on similarity.
        
        Args:
            field_type (str): The unsupported field type
            
        Returns:
            str: Suggested correction or None
        """
        if not field_type:
            return None
            
        field_type_lower = field_type.lower().strip()
        
        # Common typos and variations
        suggestions = {
            'selectone': 'select_one',
            'select one': 'select_one',
            'selectmultiple': 'select_multiple',
            'select multiple': 'select_multiple',
            'begingroup': 'begin_group',
            'begin group': 'begin_group',
            'endgroup': 'end_group',
            'end group': 'end_group',
            'int': 'integer',
            'float': 'decimal',
            'string': 'text',
        }
        
        return suggestions.get(field_type_lower)
   
