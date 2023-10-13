import pandas as pd
import os, sys, glob, logging, traceback
import numpy as np
from tqdm import tqdm
from pyxform import xls2xform
from pyxform.validators import odk_validate
import string_util as su

def process_xlsform_files(input_folder):
    processed_xlsforms = []
    processed_xlsforms_md_entries = []
    with tqdm(total=len([f for f in os.listdir(input_folder) if f.endswith('.xlsx')]), desc="Processing XLSForm Excel files", dynamic_ncols=True) as pbar:
        for file_name in os.listdir(input_folder):
            if file_name.endswith('.xlsx'):
                logging.info(f'Processing {file_name}...')
                try:
                    df_survey, df_choices, short_name, short_id, version, title = process_xlsform(input_folder, file_name)
                    processed_xlsforms.append((file_name, df_survey, df_choices, short_name, short_id, version, title))
                    processed_xlsforms_md_entries.append({'short_name': short_name, 'short_id': short_id, 'version': version})
                    pbar.update(1)
                except Exception as e:
                    logging.error(f'Error processing {file_name}: {str(e)}')
                    logging.error(traceback.format_exc())
                logging.info(f'Processed {file_name}...')
    return processed_xlsforms, processed_xlsforms_md_entries

def process_xlsform(input_folder: str, file_name: str):
    # Load the data from the xlsform, and trim all pre and trailing white spaces for strings 
    df_survey = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='survey').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_choices = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='choices').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_settings = pd.read_excel(os.path.join(input_folder, file_name), header=0, sheet_name='settings').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Parsing DSCN/LPDS version
    try:
        version_val = df_settings["version"].values[0]
        if version_val is None:
            raise ValueError('XLSForm setting version is missing.')
        elif isinstance(version_val, str):
            raise TypeError('XLSForm setting version does not conform to the convention for. Should be a number.')
        
        elif np.issubdtype(version_val.dtype, np.number) and version_val >= 0:
                version_val = int(version_val) if version_val.is_integer() else version_val
                version = str(version_val)
        else:
            raise TypeError('XLSForm setting version is of unexpected type.')
    except (ValueError, TypeError) as e:
        logging.exception(f'Caught an error in {file_name}')
        raise  

    # Parsing DSCN/LPDS tool_short_form 
    try:
        tool_name = df_settings['tool_short_form'].values[0]
        if tool_name is None:
            raise ValueError('XLSForm setting tool_short_name is missing.')
        elif isinstance(tool_name, str):
            # if tool_short_name is of type string it can be used for furter processing. This field is used for the id's, and FHIR ids only allow ASCII letters (A-Z, a-z), numbers (0-9), hyphen, and dots (.), with a length limit of 64 characters.
            short_name = tool_name.replace(" ", "-").replace("_", "-")
            if su.validate_string_FHIR_id(short_name) == False:
               logging.warning(f'{file_name}: XLSForm setting tool_short_name cannot be used for FHIR ids because it does not hold only ASCII letters, numbers, hyphen, and dots')   
        else:
            raise TypeError('XLSForm setting tool_short_name is of unexpected type.')
    except (ValueError, TypeError) as e:
        logging.exception(f'Caught an error in {file_name}')
        raise      

    # Parsing DSCN/LPDS long name from form_title
    try:
        form_title = df_settings['form_title'].values[0]
        if form_title is None:
            raise ValueError('XLSForm setting form_title is missing.')
        elif isinstance(form_title, str):
            title = form_title
        else:
            raise TypeError('XLSForm setting form_title is of unexpected type.')
    except (ValueError, TypeError) as e:
        logging.exception(f'Caught an error in {file_name}')
        raise      

    # Parsing DSCN/LPDS form_id
    try:
        form_id = df_settings['form_id'].values[0]
        if form_title is None:
            raise ValueError('XLSForm setting form_title is missing.')
        elif isinstance(form_id, str):
            short_id = form_id.replace(" ", "-").replace("_", "-")  
        else:
            raise TypeError('XLSForm setting form_id is of unexpected type.')
    except (ValueError, TypeError) as e:
        logging.exception(f'Caught an error in {file_name}')
        raise      

    return df_survey, df_choices, short_name, short_id, version, title

def convert_to_xform_and_validate(input_folder: str, output_folder: str) -> None:
    logging.info('Checking input XLSForms by converting them to XForm using pyxfrom libary...')
    # Get list of all .xlsx files in the input folder
    xls_files = glob.glob(input_folder + "*.xlsx")

    if not os.path.exists(f"{output_folder}xform"):
        os.makedirs(f"{output_folder}xform")
        
        print(f"Created {output_folder}xform folder")
        logging.info(f"Created {output_folder}xform folder")
    
    print('Validating XSLForms by converting to XForms...')
    logging.info('Validating XSLForms by converting to XForms...')
    
    # Loop through all .xlsx files
    
    for xls_file in tqdm(xls_files):
        # Create output file path by replacing .xlsx with .xml and changing the directory
        output_file = output_folder + "xform/" + xls_file.split('\\')[-1].replace('.xlsx', '.xml')
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
