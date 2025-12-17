import logging
import os
import subprocess
import src.file_writer as fw
import src.initialization as initialization
import src.xlsform_processor as xls
import src.xlsform_to_fsh_converter as fsh
from pathlib import Path
from src.constants import LPDS_HEALTHBOARD_ABBREVIATION_DICT

input_folder = 'input/'
output_folder = 'output/'
terminology_folder = 'input/fsh/terminology'
questionnaire_folder = 'input/fsh/questionnaires'
dscn_folder = Path(output_folder) / "DSCN"
lpds_folder = Path(output_folder) / "LPDS"
processed_xlsforms = []
processed_xlsforms_md_overview = []

print('***************************************************')
print('*                                                 *')
print('* Welcome to the XLSForm to FHIR Conversion Tool! *')
print('*                                                 *')
print('***************************************************')

print('Step 0 - Setup and validation')
initialization.delete_output_folder_contents(output_folder)
initialization.initiate_logging(output_folder)

XLS_Forms = xls.read_xlsforms(input_folder, LPDS_HEALTHBOARD_ABBREVIATION_DICT)

print('Step 1 - Parse XLSForms')
processed_xlsforms, processed_xlsforms_md_overview = xls.read_and_process_xlsform_files(XLS_Forms)

print('Step 2 - Convert to FSH lines')
fsh_lines_list_DSCN, fsh_lines_list_LPDS  = fsh.convert_to_fsh(processed_xlsforms)

print('Step 3 - Writing to FSH files')
fw.write_fsh_files(fsh_lines_list_DSCN, output_folder, LPDS_HEALTHBOARD_ABBREVIATION_DICT)
fw.write_fsh_files(fsh_lines_list_LPDS, output_folder, LPDS_HEALTHBOARD_ABBREVIATION_DICT)
fw.write_to_md_file(processed_xlsforms_md_overview, os.path.join(output_folder, 'Overview of processed XLSForms.md'))
logging.info('Conversion to FSH done!')

print('Step 4 - Convert FSH files to FHIR')
logging.info('Converting FSH to FHIR using FSH SUSHI compiler...')
folders_to_process = []

# Add DSCN folder if it exists and contains a sushi-config.yaml file
if dscn_folder.exists() and any(dscn_folder.glob('sushi-config.yaml')):
    folders_to_process.append(dscn_folder)

# Add LPDS healthboard folders if they exist and contain a sushi-config.yaml file
if lpds_folder.exists():
    lpds_healthboard_folders = [f for f in lpds_folder.iterdir() if f.is_dir() and any(f.glob('sushi-config.yaml'))]
    folders_to_process.extend(lpds_healthboard_folders)

for folder in folders_to_process:
    try:
        subprocess.run('sushi', check=True, shell=True, cwd=folder)
        logging.info(f'SUSHI run successfully in {folder}')
    except subprocess.CalledProcessError as e:
        logging.error(f'Error running Sushi in {folder}: {str(e)}')
        print(f'Command failed with error: {e.returncode} in {folder}')

print('Done! Thank you for using XLSForm to FHIR today.')
logging.info('Done! Thank you for using XLSForm to FSH to FHIR today.')
