from typing import List
import glob, logging, traceback
from tqdm import tqdm
import string_util as su
from Classes.XLS_Form import XLS_Form

def read_and_process_xlsform_files(XLS_Forms: List[XLS_Form]):
    processed_xlsforms_md_entries = []
    
    for xlsForm in XLS_Forms:
        logging.info(f'Processing {xlsForm.file_name}...')
        try:
            md_entry = {'short_name': xlsForm.short_name, 'short_id': xlsForm.short_id, 'version': xlsForm.version, 'title': xlsForm.title}
            if xlsForm.lpds_healthboard_abbreviation is not None:
                md_entry['lpds_healthboard_abbreviation'] = xlsForm.lpds_healthboard_abbreviation
            processed_xlsforms_md_entries.append(md_entry)

        except Exception as e:
            logging.error(f'Error processing {xlsForm.file_name}: {str(e)}')
            logging.error(traceback.format_exc())     
        logging.info(f'Processed {xlsForm.file_name}...')            
    
    processed_xlsforms_md_overview = create_processed_xlsforms_md_overview(processed_xlsforms_md_entries)
    print(processed_xlsforms_md_overview)

    return XLS_Forms, processed_xlsforms_md_overview

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

def read_xlsforms(input_folder: str, lpds_healthboard_abbreviation_dict: dict) -> None:
    logging.info('Checking input XLSForms by converting them to XForm using pyxfrom libary...')
    # Get list of all .xlsx files in the input folder
    xls_files = glob.glob(input_folder + "*.xlsx")

    XLS_Forms = []
    
    # Loop through all .xlsx files
    for xls_file in tqdm(xls_files):
        xlsForm = XLS_Form(xls_file, xls_file.split('\\')[-1], lpds_healthboard_abbreviation_dict)
        XLS_Forms.append(xlsForm)

    logging.info('XLSForms to XForm conversion and validation done!')

    return XLS_Forms