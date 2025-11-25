import re, logging
from Classes.XLS_Form import XLS_Form
import string_util as su
import pandas as pd
import terminology_util as tu

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
        # pattern to select 'select  one' and 'select one' and 'selecte one ' 
        # TODO check if regex is the way to go
        self.select_one_pattern = re.compile("select[_ ]one[_ ]?", re.IGNORECASE)

        if data.lpds_healthboard_abbreviation:
            clean_abbreviation = data.lpds_healthboard_abbreviation.replace('-', '')
            instance_id = f'{data.lpds_healthboard_abbreviation}-{data.short_name}'
            name = f'LPDS{data.lpds_healthboard_abbreviation}{questionnaire_name}'
            copyright = "The information provided in this Questionnaire may not be used to re-produce a PROM questionnaire form, this may result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
            publisher = clean_abbreviation

        else:
            instance_id = f'DataStandardsWales-PSOM-{data.short_name}'
            name = f'DataStandardsWalesPSOM{questionnaire_name}'
            copyright = "The information provided in this Questionnaire must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used." 
            publisher = "NHS Wales"

        self.lines = [
            f'Instance: {instance_id}',
            'InstanceOf: Questionnaire',
            'Usage: #definition',
            f'* title = "{data.title}"',
            f'* name = "{name}"',
            f'* version = "{data.version}"',
            f'* status = #draft',
            f'* publisher = "{publisher}"',
            f'* description = "PSOM Questionnaire: {data.title}."',
            f'* copyright = "{copyright}"',
            '',
            ]
        
        self.indent_level = 0
        for _, row in data.df_survey.iterrows():
            self.indent = '  ' * self.indent_level
            self.extension_added = False

            if pd.isna(row["format"]) and \
            (row['type'] in ['text', 'decimal', 'integer'] or self.select_one_pattern.match(row['type'])):
                logging.warning(f"Warning processing {data.short_name}: found no format for {row['name']}. ")

            if row['type'] in ['text', 'decimal', 'integer', 'begin group', 'begin_group'] or self.select_one_pattern.match(row['type']):
                self.lines.append(f'{self.indent}* item[+]')

            # Check if 'sensitive' column exists and has a truthy value
            if 'sensitive' in row and (row['sensitive'] in ['1', 'true', 'y', 'yes'] or row['sensitive'] == 1):
                if not self.extension_added:  # If no extension has been added yet
                    self.lines.append(f'{self.indent}  * extension[0].url = "http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label"')
                    self.extension_added = True  # Set to True because an extension has been added
                else:
                    self.lines.append(f'{self.indent}  * extension[+].url = "http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label"')
                self.lines.append(f'{self.indent}  * extension[=].valueCoding = http://terminology.hl7.org/CodeSystem/v3-ActCode#PDS "patient default information sensitivity"')

            if row['type'] == 'begin group' or row['type'] == 'begin_group':
                self.handle_group(row)
            elif row['type'] == 'text':
                self.handle_question(row, 'string')
            elif row['type'] in ['decimal', 'integer']:
                self.handle_question(row, row['type'])
            elif self.select_one_pattern.match(row['type']):
                self.handle_question(row, 'choice', True)
            elif row['type'] == 'end group' or row['type'] == 'end_group':
                self.indent_level -= 1
            else:
                print('Encountered not supported type found in' + data.short_name + '   ' + row['name'] )
                logging.error(f"Error processing {data.short_name}: found unsupported datatype for {row['name']}. {row['type']} is not supported (yet). ")

    def handle_group(self, row: pd.Series):
        self.lines.append(f'{self.indent}  * linkId = "{row["name"]}"')
        self.lines.append(f'{self.indent}  * text = "{su.escape_quotes(row["label"])}"')
        self.lines.append(f'{self.indent}  * type = #group')
        self.indent_level += 1
        self.lines.append('')

    def handle_question(self, row : pd.Series, type: str, anwerValueset: bool = False):
        if not self.extension_added:  
            self.lines.append(f'{self.indent}  * extension[0].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
            self.extension_added = True  
        else:
            self.lines.append(f'{self.indent}  * extension[+].url = "http://hl7.org/fhir/StructureDefinition/entryFormat"')
        self.lines.append(f'{self.indent}  * extension[=].valueString = "{row["format"]}"')
        self.lines.append(f'{self.indent}  * linkId = "{row["name"]}"')
        self.lines.append(f'{self.indent}  * text = "{su.escape_quotes(row["label"])}"')
        self.lines.append(f'{self.indent}  * type = #{type}')

        if anwerValueset:
            ValueSetName  = self.select_one_pattern.sub('', row["type"])
            ValueSetId = tu.generate_vs_or_cs_id(self.data.short_name, ValueSetName, 'VS', self.data.lpds_healthboard_abbreviation)
            self.lines.append(f'{self.indent}  * answerValueSet = Canonical({ValueSetId})')

        self.lines.append('')
   
