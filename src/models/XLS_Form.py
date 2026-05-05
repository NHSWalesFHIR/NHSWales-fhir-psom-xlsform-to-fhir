import re
import pandas as pd
import logging
import src.string_util as su
import numpy as np

class XLS_Form:
    def __init__(self, input_path: str, file_name: str, lpds_healthboard_abbreviation_dict: dict):
        """
        Represents an XLSForm. Reads the XLSForm and processes it into a XlsFormData object.

        Args:
            data (XlsFormData): The data from an XLSForm.
        """
        
        #set inpiut path
        self.input_path = input_path
        self.file_name = file_name
        self.lpds_healthboard_abbreviation_dict = lpds_healthboard_abbreviation_dict
        self.xls_form = self.xls_to_dataframe(input_path)

        # settings
        self.df_settings = self.xls_form['settings'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
        # survey
        self.df_survey = self.xls_form['survey'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
        # choices
        self.df_choices = self.xls_form['choices'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

        logging.info(f'XLSForm loaded from {input_path}')

        self.process_form()

    def process_form(self):
        # process the form
        logging.info(f'Processing form {self.input_path}')

        #data = XlsFormData(self.df_survey, self.df_choices)
        try:
            self.set_and_parse_version(self.df_settings, self.file_name)
            self.set_and_parse_short_name(self.df_settings, self.file_name)
            self.set_and_parse_title(self.df_settings, self.file_name)
            self.set_and_parse_form_id(self.df_settings, self.file_name)
            self.set_and_parse_lpds_healthboard_abbreviation(self.df_settings, self.file_name, self.lpds_healthboard_abbreviation_dict)
            self.parse_relevant_conditions()

        except (ValueError, TypeError) as e:
            logging.exception(f'Error processing {self.file_name}: {str(e)}')
            raise

    def parse_relevant_conditions(self):
        """
        Parse the 'relevant' column in the survey sheet into structured enable-when conditions.

        XLSForm expressions like:
            ${FIELD} = 'VALUE' or ${FIELD} = 'VALUE2'
        are parsed into a list of condition dicts per question name.

        Populates:
            self.enable_when_conditions : dict[str, list[dict]]
                Maps each question name to a list of conditions, where each condition is:
                    {'linkId': str, 'operator': str, 'answer': str}
            self.enable_behavior : dict[str, str]
                Maps each question name to 'any' (or-joined) or 'all' (and-joined).
        """
        self.enable_when_conditions = {}
        self.enable_behavior = {}

        # The spreadsheet may have a duplicate 'relevant' column (e.g. a legacy empty one),
        # causing pandas to rename the second to 'relevant.1'. Find the column that has data.
        relevant_col = None
        for col in self.df_survey.columns:
            if col == 'relevant' or col.startswith('relevant.'):
                if self.df_survey[col].astype(str).str.strip().ne('').any():
                    relevant_col = col
                    break
        # Fall back to the first 'relevant' column even if empty
        if relevant_col is None:
            if 'relevant' in self.df_survey.columns:
                relevant_col = 'relevant'
            else:
                logging.info(f'{self.file_name}: No "relevant" column found in survey sheet.')
                return

        if relevant_col != 'relevant':
            logging.info(f'{self.file_name}: Using column "{relevant_col}" as the relevant column (duplicate column name detected).')

        for _, row in self.df_survey.iterrows():
            name = row.get('name', '')
            relevant = row.get(relevant_col, '')

            if not isinstance(relevant, str) or relevant.strip() == '':
                continue

            parsed_relevant = self._parse_relevant_expression(relevant.strip())

            if parsed_relevant:
                self.enable_when_conditions[name] = parsed_relevant['conditions']
                self.enable_behavior[name] = parsed_relevant['behavior']
                logging.info(
                    f'{self.file_name}: Parsed {len(parsed_relevant["conditions"])} enable condition(s) '
                    f'(behavior="{parsed_relevant["behavior"]}") for question "{name}".')
            else:
                logging.error(
                    f'{self.file_name}: Could not parse relevant expression '
                    f'for question "{name}": "{relevant}"')

    def _parse_relevant_expression(self, expression: str):
        tokens = re.split(r'\s+(or)\s+', expression, flags=re.IGNORECASE)
        condition_tokens = [token.strip() for token in tokens[0::2] if token.strip()]
        connectors = [connector.lower() for connector in tokens[1::2]]

        if not condition_tokens:
            return None

        if re.search(r'\s+and\s+', expression, flags=re.IGNORECASE):
            logging.error(
                f'{self.file_name}: Only OR conditions are supported in relevant expressions: "{expression}"')
            return None

        if re.fullmatch(r'not\(.*\)', expression, flags=re.IGNORECASE) or re.fullmatch(r'\$\{[^}]+\}', expression):
            logging.error(
                f'{self.file_name}: Boolean relevant expressions are not supported: "{expression}"')
            return None

        if connectors and any(connector != 'or' for connector in connectors):
            logging.error(
                f'{self.file_name}: Only OR conditions are supported in relevant expressions: "{expression}"')
            return None

        behavior = 'any'

        conditions = []
        for token in condition_tokens:
            condition = self._parse_relevant_condition(token)
            if condition is None:
                return None
            conditions.append(condition)

        return {'conditions': conditions, 'behavior': behavior}

    def _parse_relevant_condition(self, token: str):
        if re.fullmatch(r'not\(\s*\$\{([^}]+)\}\s*\)', token, flags=re.IGNORECASE) or re.fullmatch(r'\$\{([^}]+)\}', token):
            logging.error(
                f'{self.file_name}: Boolean relevant condition syntax is not supported: "{token}"')
            return None

        comparison_match = re.fullmatch(r'\$\{([^}]+)\}\s*(=|!=|<=|>=|<|>)\s*(.+)', token)
        if not comparison_match:
            logging.error(
                f'{self.file_name}: Unsupported relevant condition syntax: "{token}"')
            return None

        answer_type, answer_value = self._parse_relevant_literal(comparison_match.group(3).strip())
        if answer_type is None:
            logging.error(
                f'{self.file_name}: Unsupported relevant literal in condition: "{token}"')
            return None

        return {
            'linkId': comparison_match.group(1),
            'operator': comparison_match.group(2),
            'answer': answer_value,
            'answer_type': answer_type
        }

    def _parse_relevant_literal(self, literal: str):
        if re.fullmatch(r"'[^']*'", literal) or re.fullmatch(r'"[^"]*"', literal):
            return 'string', literal[1:-1]

        literal_lower = literal.lower()
        if literal_lower in ['true', 'true()']:
            return 'boolean', True
        if literal_lower in ['false', 'false()']:
            return 'boolean', False

        if re.fullmatch(r'-?\d+', literal):
            return 'integer', int(literal)

        if re.fullmatch(r'-?\d+\.\d+', literal):
            return 'decimal', float(literal)

        return None, None

    def set_and_parse_version(self, df_settings: pd.DataFrame, file_name):
        try:
            version_val = df_settings["version"].values[0]
            if version_val is None:
                raise ValueError('XLSForm settings version is missing.')
            elif not np.issubdtype(type(version_val), np.number) or version_val < 0:
                raise TypeError('XLSForm settings version is not a non-negative number.')

            if isinstance(version_val, float) and version_val.is_integer():
                version_val = int(version_val)
                
            self.version = str(version_val)
        
        except (ValueError, TypeError) as e:
            logging.exception(f'Error parsing version in {file_name}: {str(e)}')
            raise 
        
    def set_and_parse_short_name(self, df_settings: pd.DataFrame, file_name):
        try:
            short_name = self.get_attribute(df_settings, 'tool_short_form')
            self.short_name = self.format_string(short_name)
            if not su.validate_string_FHIR_id(self.short_name):
                logging.warning(f'{file_name}: XLSForm settings tool_short_name cannot be used for FHIR ids.')
        
        except (ValueError, TypeError) as e:
            logging.exception(f'Error parsing tool_name in {file_name}: {str(e)}')
            raise

    def set_and_parse_title(self, df_settings: pd.DataFrame, file_name: str):
        try:
            self.title = self.get_attribute(df_settings, 'form_title')
        except (ValueError, TypeError) as e:
            logging.exception(f'Error parsing form_title in {file_name}: {str(e)}')
            raise

    def set_and_parse_form_id(self, df_settings: pd.DataFrame, file_name: str):
        try:
            short_id = self.get_attribute(df_settings, 'form_id')
            self.short_id = self.format_string(short_id)
        except (ValueError, TypeError) as e:
            logging.exception(f'Error parsing form_id in {file_name}: {str(e)}')
            raise

    def get_attribute(self, df_settings: pd.DataFrame, attribute_name: str):
        try:
            # Check if the column exists first
            if attribute_name not in df_settings.columns:
                raise ValueError(f'XLSForm settings column "{attribute_name}" is missing from the settings sheet.')
            
            attribute = df_settings[attribute_name].values[0]
            
            # Only check for None/empty, let calling methods handle type validation
            if attribute is None or (isinstance(attribute, str) and attribute.strip() == ""):
                raise ValueError(f'XLSForm settings {attribute_name} is missing or empty.')
            
        except (ValueError, KeyError) as e:
            logging.error(f'Error getting attribute {attribute_name}: {str(e)}')
            raise

        return attribute
    
    def set_and_parse_lpds_healthboard_abbreviation(self, df_settings, file_name, lpds_healthboard_abbreviation_dict):
        lpds_healthboard_abbreviation = None

        if 'lpds_healthboard_abbreviation' in df_settings:
            lpds_healthboard_abbreviation = df_settings['lpds_healthboard_abbreviation'].values[0]

            # Convert to string if not None
            if lpds_healthboard_abbreviation is not None:
                lpds_healthboard_abbreviation = str(lpds_healthboard_abbreviation)

                if lpds_healthboard_abbreviation.strip() == "":
                    logging.error(f'{file_name}: lpds_healthboard_abbreviation column is provided but the value is empty.')
                    raise ValueError('lpds_healthboard_abbreviation column is provided but the value is empty.')
                
                if not lpds_healthboard_abbreviation.isalnum():
                    logging.error(f'{file_name}: XLSForm settings lpds_healthboard_abbreviation contains invalid characters. Only letters and numbers are allowed.')
                    raise TypeError('XLSForm settings lpds_healthboard_abbreviation contains invalid characters. Only letters and numbers are allowed.')

                valid_keys = ", ".join(lpds_healthboard_abbreviation_dict.keys())
                if lpds_healthboard_abbreviation not in lpds_healthboard_abbreviation_dict:
                    logging.error(f"{file_name}: lpds_healthboard_abbreviation '{lpds_healthboard_abbreviation}' is not a valid abbreviation. Valid abbreviations are: {valid_keys}.")
                    raise ValueError(f"lpds_healthboard_abbreviation '{lpds_healthboard_abbreviation}' is not a valid abbreviation. Valid abbreviations are: {valid_keys}.")
                
                if not su.validate_string_FHIR_id(lpds_healthboard_abbreviation):
                    logging.warning(f'{file_name}: XLSForm settings lpds_healthboard_abbreviation cannot be used for FHIR ids. Making FHIR id compliant')
                    lpds_healthboard_abbreviation = su.make_fhir_compliant(lpds_healthboard_abbreviation)
                
                lpds_healthboard_abbreviation = lpds_healthboard_abbreviation.replace(" ", "-").replace("_", "-")

        self.lpds_healthboard_abbreviation = lpds_healthboard_abbreviation
    
    def __str__(self):
        return f"Name: {self.name}\nData: {self.data}"
    
    def format_string(self, string: str):
        return string.replace(" ", "-").replace("_", "-")
    
    def xls_to_dataframe(self, input: str):
        df = pd.DataFrame()
        try:
            df = pd.read_excel(input, sheet_name=None, keep_default_na=False)
        except Exception as e:
            logging.error(f'Error while converting {self.input_path} to XForm: {str(e)}')
        return df