import pandas as pd
import logging
from Classes.XlsFormData import XlsFormData

class XLS_Form:
    def __init__(self, input_path: str, file_name: str, lpds_healthboard_abbreviation_dict: dict):
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

        self.data = self.process_form()


    def process_form(self):
        # process the form
        logging.info(f'Processing form {self.input_path}')

        data = XlsFormData(self.df_survey, self.df_choices)
        try:
            data.set_and_parse_version(self.df_settings, self.file_name)
            data.set_and_parse_short_name(self.df_settings, self.file_name)
            data.set_and_parse_title(self.df_settings, self.file_name)
            data.set_and_parse_form_id(self.df_settings, self.file_name)
            data.set_and_parse_lpds_healthboard_abbreviation(self.df_settings, self.file_name, self.lpds_healthboard_abbreviation_dict)

        except (ValueError, TypeError) as e:
            logging.exception(f'Error processing {self.file_name}: {str(e)}')
            raise

        return data


    def __str__(self):
        return f"Name: {self.name}\nData: {self.data}"
    
    def xls_to_dataframe(self, input: str):
        df = pd.DataFrame()
        try:
            df = pd.read_excel(input, sheet_name=None, keep_default_na=False)
        except Exception as e:
            logging.error(f'Error while converting {self.input_path} to XForm: {str(e)}')
        return df