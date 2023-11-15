import pandas as pd
import os, sys, glob, logging, traceback
import numpy as np
from tqdm import tqdm
from pyxform import xls2xform
from pyxform.validators import odk_validate
import string_util as su

def conversion_context():
    while True:
        user_choice = input('Would you like to convert a DSCN or LPDS? (dscn/lpds): ').lower()

        if user_choice == 'lpds':
            return 'lpds'
        elif user_choice == 'dscn':
            return 'dscn'
        else:
            print('Invalid choice. Please enter "yes" or "no".')

def process_xlsform_files(input_folder, user_choice):
    processed_xlsforms = []
    processed_xlsforms_md_entries = []
    with tqdm(total=len([f for f in os.listdir(input_folder) if f.endswith('.xlsx')]), desc="Processing XLSForm Excel files", dynamic_ncols=True) as pbar:
        for file_name in os.listdir(input_folder):
            if file_name.endswith('.xlsx'):
                logging.info(f'Processing {file_name}...')
                try:
                    if user_choice == 'lpds':
                        print(' Parsing of the XLSForm following the LPDS settings.')
                        df_survey, df_choices, short_name, short_id, version, title, healthboard_abbreviation = process_lpds_xlsform(input_folder, file_name)
                        processed_xlsforms.append((file_name, df_survey, df_choices, short_name, short_id, version, title, healthboard_abbreviation))
                        processed_xlsforms_md_entries.append({'short_name': short_name, 'short_id': short_id, 'version': version, 'healthboard_abbreviation': healthboard_abbreviation})
                        pbar.update(1)
                    elif user_choice == 'dscn':
                        print(' Parsing of the XLSForm following the DSCN settings.')
                        df_survey, df_choices, short_name, short_id, version, title = process_dscn_xlsform(input_folder, file_name)
                        processed_xlsforms.append((file_name, df_survey, df_choices, short_name, short_id, version, title))
                        processed_xlsforms_md_entries.append({'short_name': short_name, 'short_id': short_id, 'version': version})
                        pbar.update(1)
                except Exception as e:
                    logging.error(f'Error processing {file_name}: {str(e)}')
                    logging.error(traceback.format_exc())     
                logging.info(f'Processed {file_name}...')            
    return processed_xlsforms, processed_xlsforms_md_entries


def process_lpds_xlsform(input_folder: str, file_name: str):
    df_survey, df_choices, df_settings = load_xlsform_data(input_folder, file_name)

    try:
        version, short_name, title, short_id, hb_abbrev = parsing_version(df_settings, file_name), parsing_tool_name(df_settings, file_name), parsing_form_title(df_settings, file_name), parsing_form_id(df_settings, file_name), parsing_hb_abbrev(df_settings, file_name)
    except (ValueError, TypeError) as e:
        logging.exception(f'Error processing {file_name}: {str(e)}')
        raise

    return df_survey, df_choices, short_name, short_id, version, title, hb_abbrev


def process_dscn_xlsform(input_folder: str, file_name: str):
    df_survey, df_choices, df_settings = load_xlsform_data(input_folder, file_name)

    try:
        version, short_name, title, short_id = parsing_version(df_settings, file_name), parsing_tool_name(df_settings, file_name), parsing_form_title(df_settings, file_name), parsing_form_id(df_settings, file_name)
    except (ValueError, TypeError) as e:
        logging.exception(f'Error processing {file_name}: {str(e)}')
        raise

    return df_survey, df_choices, short_name, short_id, version, title


def load_xlsform_data(input_folder: str, file_name: str):
    df_survey = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='survey').map(lambda x: x.strip() if isinstance(x, str) else x)
    df_choices = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='choices').map(lambda x: x.strip() if isinstance(x, str) else x)
    df_settings = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='settings').map(lambda x: x.strip() if isinstance(x, str) else x)

    return df_survey, df_choices, df_settings


def parsing_version(df_settings, file_name):
    try:
        version_val = df_settings["version"].values[0]
        if version_val is None:
            raise ValueError('XLSForm setting version is missing.')
        elif not np.issubdtype(type(version_val), np.number) or version_val < 0:
            raise TypeError('XLSForm setting version is not a non-negative number.')

        version_val = int(version_val) if version_val.is_integer() else version_val
        return str(version_val)
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing version in {file_name}: {str(e)}')
        raise


def parsing_tool_name(df_settings, file_name):
    try:
        tool_name = df_settings['tool_short_form'].values[0]
        if tool_name is None:
            raise ValueError('XLSForm setting tool_short_name is missing.')
        elif not isinstance(tool_name, str):
            raise TypeError('XLSForm setting tool_short_name is not a string.')

        short_name = tool_name.replace(" ", "-").replace("_", "-")
        if not su.validate_string_FHIR_id(short_name):
            logging.warning(f'{file_name}: XLSForm setting tool_short_name cannot be used for FHIR ids.')
        return short_name
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing tool_name in {file_name}: {str(e)}')
        raise


def parsing_form_title(df_settings, file_name):
    try:
        form_title = df_settings['form_title'].values[0]
        if form_title is None:
            raise ValueError('XLSForm setting form_title is missing.')
        elif not isinstance(form_title, str):
            raise TypeError('XLSForm setting form_title is not a string.')

        return form_title
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing form_title in {file_name}: {str(e)}')
        raise


def parsing_form_id(df_settings, file_name):
    try:
        form_id = df_settings['form_id'].values[0]
        if form_id is None:
            raise ValueError('XLSForm setting form_id is missing.')
        elif not isinstance(form_id, str):
            raise TypeError('XLSForm setting form_id is not a string.')

        return form_id.replace(" ", "-").replace("_", "-")
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing form_id in {file_name}: {str(e)}')
        raise


def parsing_hb_abbrev(df_settings, file_name):
    try:
        hb_abbrev = df_settings['healthboard_abbreviation'].values[0]
        if hb_abbrev is None:
            raise ValueError('XLSForm setting hb_abbrev is missing.')
        elif not isinstance(hb_abbrev, str):
            raise TypeError('XLSForm setting hb_abbrev is not a string.')

        hb_abbrev = hb_abbrev.replace(" ", "-").replace("_", "-")
        if not su.validate_string_FHIR_id(hb_abbrev):
            logging.warning(f'{file_name}: XLSForm setting hb_abbrev cannot be used for FHIR ids.')
        return hb_abbrev
    except (ValueError, TypeError) as e:
        logging.exception(f'Error parsing hb_abbrev in {file_name}: {str(e)}')
        raise

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

