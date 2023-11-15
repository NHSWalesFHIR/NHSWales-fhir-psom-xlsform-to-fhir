import re, os, sys, logging, shutil, traceback, subprocess
import xlsform_processor as xls
import xlsform_to_fsh_converter as fsh
import file_writer as fw
import setup

"""
Author  Version    Date        Comment
--------------------------------------------------------------------------------------------------------
Firely  1.0.0-rc1  2023-09-26  Moved codebase to dedicatied repository. Refactored code to work within
                               the input and output folders. Configured SUSHI within the output folder.
---------------------------------------------------------------------------------------------------------
"""

__version__ = '1.0.0-rc'
input_folder = 'input/'
output_folder = 'output/'
terminology_folder = 'input/fsh/terminology'
questionnaire_folder = 'input/fsh/questionnaires'
processed_xlsforms = []
processed_xlsforms_md_overview = []
fsh_lines_list = []
lpds_healthboard_abbreviation_dict = {
    "BCU": "https://fhir.bcuhb.nhs.wales/",
    "ABU": "https://fhir.abuhb.nhs.wales/",
    "CAV": "https://fhir.cavuhb.nhs.wales/",
    "CTM": "https://fhir.ctmuhb.nhs.wales/",
    "HDU": "https://fhir.hduhb.nhs.wales/",
    "PTH": "https://fhir.pthb.nhs.wales/",
    "SBU": "https://fhir.sbuhb.nhs.wales/",
    "VUH": "https://fhir.vunhst.nhs.wales/"
}

# TODO insert mapping of abbriviation to canonical base so post sushi step is not needed
# TODO update documentation


print('***************************************************')
print('*                                                 *')
print('* Welcome to the XLSForm to FHIR Conversion Tool! *')
print('*                                                 *')
print('****************************************************')

print('Step 0 - Setup and validation')
setup.delete_output_folder_contents(output_folder + questionnaire_folder)
setup.delete_output_folder_contents(output_folder + terminology_folder)
setup.delete_output_folder_contents(output_folder + 'XForm')
setup.initiate_logging(output_folder)
xls.convert_to_xform_and_validate(input_folder, output_folder)

print('Step 1 - Parse XLSForms')
processed_xlsforms, processed_xlsforms_md_overview = xls.process_xlsform_files(input_folder, lpds_healthboard_abbreviation_dict)

print('Step 2 - Convert to FSH lines')
fsh_lines_list = fsh.convert_to_fsh(processed_xlsforms)

print('Step 3 - Writing to FSH files')
fw.write_fsh_files(fsh_lines_list, output_folder, terminology_folder, questionnaire_folder)
fw.write_to_md_file(processed_xlsforms_md_overview, os.path.join(output_folder, 'Overview of processed XLSForms.md'))
logging.info('Conversion to FSH done!')

print('Step 4 - Convert FSH files to FHIR')
logging.info('Converting FSH to FHIR using FSH SUSHI compiler...')
try:
    subprocess.run('sushi', check=True, shell=True, cwd='output/')
except subprocess.CalledProcessError as e:
    logging.error(f'Error running Sushi: {str(e)}')
    print(f'Command failed with error: {e.returncode}')

print('Done! Thank you for using XLSForm to FHIR today.')
logging.info('Done! Thank you for using XLSForm to FSH to FHIR today.')
