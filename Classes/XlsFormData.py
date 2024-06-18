import numpy as np
import string_util as su
import pandas as pd
import logging

class XlsFormData:

    def __init__(self, df_survey: pd.DataFrame, df_choices: pd.DataFrame):
        self.df_survey = df_survey
        self.df_choices = df_choices

    def get_attribute(self, df_settings: pd.DataFrame, attribute_name: str):
        try:
            attribute = df_settings[attribute_name].values[0]
            if attribute is None:
                raise ValueError(f'XLSForm settings {attribute_name} is missing.')
            elif not isinstance(attribute_name, str):
                raise TypeError(f'XLSForm settings {attribute_name} is not of type string.')
            
        except (ValueError, TypeError) as e:
            return e

        return attribute
    
    def format_string(self, string: str):
        return string.replace(" ", "-").replace("_", "-")

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
                
                if not lpds_healthboard_abbreviation.isalpha():
                    logging.error(f'{file_name}: XLSForm settings lpds_healthboard_abbreviation is not a string.')
                    raise TypeError('XLSForm settings lpds_healthboard_abbreviation is not a string.')

                valid_keys = ", ".join(lpds_healthboard_abbreviation_dict.keys())
                if lpds_healthboard_abbreviation not in lpds_healthboard_abbreviation_dict:
                    logging.error(f"{file_name}: lpds_healthboard_abbreviation '{lpds_healthboard_abbreviation}' is not a valid abbreviation. Valid abbreviation are: {valid_keys}.")
                
                if not su.validate_string_FHIR_id(lpds_healthboard_abbreviation):
                    logging.warning(f'{file_name}: XLSForm settings lpds_healthboard_abbreviation cannot be used for FHIR ids. Making FHIR id compliant')
                    lpds_healthboard_abbreviation = su.make_fhir_compliant(lpds_healthboard_abbreviation)
                
                lpds_healthboard_abbreviation = lpds_healthboard_abbreviation.replace(" ", "-").replace("_", "-")

        self.lpds_healthboard_abbreviation = lpds_healthboard_abbreviation

