import re, os, sys, logging, shutil, traceback, subprocess
from pathlib import Path
import xlsform_processor as xls
import xlsform_to_fsh_converter as fsh
import file_writer as fw
import setup

"""
Author  Version    Date         Comment
---------------------------------------------------------------------------------------------------------
Firely  1.0.0-rc1  2023-09-26   Moved codebase to dedicatied repository. Refactored code to work within
                                the input and output folders. Configured SUSHI within the output folder.
Firely  1.0.0-rc2               Support for DSCN and LPDS processing. 
                                Updated to latest naming conventions for resource identities.
                                Improved output overview file containig what has been processed. 
                                Removed the creation of QuestionReferene CodeSystems and ValueSet

---------------------------------------------------------------------------------------------------------
"""

__version__ = '1.0.0-rc2'
input_folder = 'input/'
output_folder = 'output/'
terminology_folder = 'input/fsh/terminology'
questionnaire_folder = 'input/fsh/questionnaires'
dscn_folder = Path(output_folder) / "DSCN"
lpds_folder = Path(output_folder) / "LPDS"
processed_xlsforms = []
processed_xlsforms_md_overview = []
fsh_lines_list = []
lpds_healthboard_abbreviation_dict = {
    "ABU": "https://fhir.abuhb.nhs.wales/",
    "BCU": "https://fhir.bcuhb.nhs.wales/",
    "CAV": "https://fhir.cavuhb.nhs.wales/",
    "CTM": "https://fhir.ctmuhb.nhs.wales/",
    "HDU": "https://fhir.hduhb.nhs.wales/",
    "PTH": "https://fhir.pthb.nhs.wales/",
    "SBU": "https://fhir.sbuhb.nhs.wales/",
    "VUH": "https://fhir.vunhst.nhs.wales/"
}

print('***************************************************')
print('*                                                 *')
print('* Welcome to the XLSForm to FHIR Conversion Tool! *')
print('*                                                 *')
print('***************************************************')

print('Step 0 - Setup and validation')
setup.delete_output_folder_contents(output_folder)
setup.initiate_logging(output_folder)
xls.convert_to_xform_and_validate(input_folder, output_folder)

print('Step 1 - Parse XLSForms')
processed_xlsforms, processed_xlsforms_md_overview = xls.process_xlsform_files(input_folder, lpds_healthboard_abbreviation_dict)

print('Step 2 - Convert to FSH lines')
fsh_lines_list = fsh.convert_to_fsh(processed_xlsforms)

print('Step 3 - Writing to FSH files')
fw.write_fsh_files(fsh_lines_list, output_folder, lpds_healthboard_abbreviation_dict)
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
