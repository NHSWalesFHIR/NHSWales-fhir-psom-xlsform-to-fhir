import pandas as pd
import os, sys, glob, logging, traceback
import numpy as np
from tqdm import tqdm
from pyxform import xls2xform
from pyxform.validators import odk_validate
import string_util as su

def process_xlsform_files(input_folder, lpds_healthboard_abbreviation_dict):
    processed_xlsforms = []
    processed_xlsforms_md_entries = []
    with tqdm(total=len([f for f in os.listdir(input_folder) if f.endswith('.xlsx')]), desc="Processing XLSForm Excel files", dynamic_ncols=True) as pbar:
        for file_name in os.listdir(input_folder):
            if file_name.endswith('.xlsx'):
                logging.info(f'Processing {file_name}...')
                try:
                        df_survey, df_choices, short_name, short_id, version, title, lpds_healthboard_abbreviation = process_xlsform(input_folder, file_name, lpds_healthboard_abbreviation_dict)
                        processed_xlsforms.append((file_name, df_survey, df_choices, short_name, short_id, version, title, lpds_healthboard_abbreviation))
                        
                        md_entry = {'short_name': short_name, 'short_id': short_id, 'version': version, 'title': title}
                        if lpds_healthboard_abbreviation is not None:
                            md_entry['lpds_healthboard_abbreviation'] = lpds_healthboard_abbreviation
                        processed_xlsforms_md_entries.append(md_entry)

                        pbar.update(1)
                except Exception as e:
                    logging.error(f'Error processing {file_name}: {str(e)}')
                    logging.error(traceback.format_exc())     
                logging.info(f'Processed {file_name}...')            
    
    processed_xlsforms_md_overview = create_processed_xlsforms_md_overview(processed_xlsforms_md_entries)
    print(processed_xlsforms_md_overview)

    return processed_xlsforms, processed_xlsforms_md_overview

def create_processed_xlsforms_md_overview(processed_xlsforms_md_entries: list) -> str:
    processed_lpds = sorted(
        [entry for entry in processed_xlsforms_md_entries if 'lpds_healthboard_abbreviation' in entry],
        key=lambda x: (x['lpds_healthboard_abbreviation'], x['short_name'])
    )
    processed_dscn = sorted(
        [entry for entry in processed_xlsforms_md_entries if 'lpds_healthboard_abbreviation' not in entry],
        key=lambda x: x['short_name']
    )
    number_of_processed_lpds = len(processed_lpds)
    number_of_processed_dscn = len(processed_dscn)
    
    md_lines = "# XLSForm PROMs to FHIR transformation results\n\n"
    md_lines += f"## Processed {number_of_processed_dscn} DSCN XLSForms\n"
    for entry in processed_dscn:
        md_lines += f"- **{entry['short_name']}** ({entry['short_id']}) - {entry['version']}\n"
    
    md_lines += f"\n## Processed {number_of_processed_lpds} LPDS XLSForms\n"
    for entry in processed_lpds:
        md_lines += f"{entry['lpds_healthboard_abbreviation']}: **{entry['short_name']}** ({entry['short_id']}) - {entry['version']}\n"
    
    return md_lines


def load_xlsform_data(input_folder: str, file_name: str):
    """
    Loads XLSForm data from a specified Excel file located in the given input folder.
    
    This function reads the 'survey', 'choices', and 'settings' sheets from the specified 
    Excel file. Each cell in these sheets is processed to strip leading and trailing whitespace
    if the cell contains a string. Other data types in the cells are left unchanged.

    Parameters:
    - input_folder (str): The folder path where the Excel file is located.
    - file_name (str): The name of the Excel file to be loaded.

    Returns:
    tuple: A tuple containing three pandas DataFrames corresponding to the 'survey', 
           'choices', and 'settings' sheets of the Excel file, respectively.
    """

    xls = pd.read_excel(os.path.join(input_folder, file_name), sheet_name=None, keep_default_na=False)
    df_survey = xls['survey'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_choices = xls['choices'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_settings = xls['settings'].apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

    return df_survey, df_choices, df_settings

def process_xlsform(input_folder: str, file_name: str, lpds_healthboard_abbreviation_dict: dict):
    df_survey, df_choices, df_settings = load_xlsform_data(input_folder, file_name)

    try:
        version, short_name, title, short_id, lpds_healthboard_abbreviation = parsing_version(df_settings, file_name), parsing_tool_short_form(df_settings, file_name), parsing_form_title(df_settings, file_name), parsing_form_id(df_settings, file_name), parsing_lpds_healthboard_abbreviation(df_settings, file_name, lpds_healthboard_abbreviation_dict)
    except (ValueError, TypeError) as e:
        logging.exception(f'Error processing {file_name}: {str(e)}')
        raise

    return df_survey, df_choices, short_name, short_id, version, title, lpds_healthboard_abbreviation

def parsing_version(df_settings, file_name):
    try:
        version_val = df_settings["version"].values[0]
        if version_val is None:
            raise ValueError('XLSForm settings version is missing.')
        elif not np.issubdtype(type(version_val), np.number) or version_val < 0:
            raise TypeError('XLSForm settings version is not a non-negative number.')

        if isinstance(version_val, float) and version_val.is_integer():
            version_val = int(version_val)
            
        return str(version_val)
    
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing version in {file_name}: {str(e)}')
        raise
    

def parsing_tool_short_form(df_settings, file_name):
    try:
        tool_name = df_settings['tool_short_form'].values[0]
        if tool_name is None:
            raise ValueError('XLSForm settings tool_short_name is missing.')
        elif not isinstance(tool_name, str):
            raise TypeError('XLSForm settings tool_short_name is not a string.')

        short_name = tool_name.replace(" ", "-").replace("_", "-")
        if not su.validate_string_FHIR_id(short_name):
            logging.warning(f'{file_name}: XLSForm settings tool_short_name cannot be used for FHIR ids.')
        return str(short_name)
    
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing tool_name in {file_name}: {str(e)}')
        raise

def parsing_form_title(df_settings, file_name):
    try:
        form_title = df_settings['form_title'].values[0]
        if form_title is None:
            raise ValueError('XLSForm settings form_title is missing.')
        elif not isinstance(form_title, str):
            raise TypeError('XLSForm settings form_title is not a string.')

        return str(form_title)
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing form_title in {file_name}: {str(e)}')
        raise

def parsing_form_id(df_settings, file_name):
    try:
        form_id = df_settings['form_id'].values[0]
        if form_id is None:
            raise ValueError('XLSForm settings form_id is missing.')
        elif not isinstance(form_id, str):
            raise TypeError('XLSForm settings form_id is not a string.')

        return str(form_id.replace(" ", "-").replace("_", "-"))
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing form_id in {file_name}: {str(e)}')
        raise

def parsing_lpds_healthboard_abbreviation(df_settings, file_name, lpds_healthboard_abbreviation_dict):
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

    return lpds_healthboard_abbreviation

def convert_to_xform_and_validate(input_folder: str, output_folder: str) -> None:
    logging.info('Checking input XLSForms by converting them to XForm using pyxfrom libary...')
    # Get list of all .xlsx files in the input folder
    xls_files = glob.glob(input_folder + "*.xlsx")

    if not os.path.exists(f"{output_folder}XForm"):
        os.makedirs(f"{output_folder}XForm")
        
        print(f"Created {output_folder}XForm folder")
        logging.info(f"Created {output_folder}XForm folder")
    
    print('Validating XSLForms by converting to XForms...')
    logging.info('Validating XSLForms by converting to XForms...')
    
    # Loop through all .xlsx files
    
    for xls_file in tqdm(xls_files):
        # Create output file path by replacing .xlsx with .xml and changing the directory
        output_file = output_folder + "XForm/" + xls_file.split('\\')[-1].replace('.xlsx', '.xml')
        convert_to_xform(xls_file, output_file)

    logging.info('XLSForms to XForm conversion and validation done!')

    # Validation of XForm is turned off for now because it didn't work on all tested machines yet.  
    #print('Validating XForms...')
    #logging.info('Validating XForms...')
    #xform_files = glob.glob(input_folder + 'XForm/' + "*.xml")
    #for x_file in tqdm(xform_files):
    #    # Create output file path by replacing .xlsx with .xml and changing the directory
    #    output_file = input_folder + "XForm/" + x_file
    #    validate_xform(output_file)

def convert_to_xform(input_path, output_path):
    try:
        xls2xform.xls2xform_convert(input_path, output_path, validate=False)
        logging.info(f"Converted {input_path} to XForm successfully.")
    except Exception as e:
        logging.error(f"Error occurred while converting {output_path} to XForm: {str(e)}")
        return str(e)

def validate_xform(xform_path):
    try:
        xform_warnings = odk_validate.check_xform(xform_path)
        if len(xform_warnings) == 0:
            logging.info(f"{xform_path} XForm is valid with no warnings!")
        else:
            logging.warning(f"{xform_path} XForm is valid but has warnings.")
            logging.warning(xform_warnings)
        return xform_warnings
    except Exception as e:
        logging.error(f"Error occurred while checking {xform_path} xform: {str(e)}")
        return str(e)

