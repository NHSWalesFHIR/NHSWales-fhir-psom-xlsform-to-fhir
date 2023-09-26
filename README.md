# XLSForm to FSH to FHIR Converter
This script is used to convert XLSForm files into FHIR Shorthand (FSH) format followed by transformation to FHIR. The XLSForm files can be DSCN or LPDS.

## How it Works
The script has an `input/` and `output/` folder. It performs the following steps:

1. Prepares Output Folders: **Removes** and recreates folders in the specified output directory.

2. Processes XLSForms: Reads XLSForm files (.xlsx) from a specified input folder. It transforms it to XForm for additional validation, and logs encounterd issues. For each XLSForm, it:

3. Extracts the survey and choices data, as well as the short name, short ID, version, and title of the form.
 - Creates FSH for questionnaires and terminology using the extracted information.
 - Writes the FSH data to files in the `output/input/fsh/questionnaires` and `output/input/fsh/terminology` folders respectively.
 - Logs Information and Errors: Logs information such as the start of the conversion, the processing of each file, and any errors that occur. Logs are written to `log_file.txt` in the specified output directory.

4. Triggers SUSHI to transform the contents in `output/input/fsh/` to FHIR in the `output/fsh-generated/` folder. The output contents can then be copied/moved to their respective repositories. 

## Supported XLSForm types
It supports the conversion of the following XLSForm types:
* text
* select_one
* decimal
* integer
* begin group

## How to Use
To use the script, make sure you have all the required dependencies (see below) and that the variables in `main.py` for the `input_folder` and `output_folder` are correct paths that are used on your local machine. Then, simply run the script. It will process all XLSForm files in the input directory and write the resulting FSH data to the output directory, while also logging its operation.

## File Descriptions
- `main.py`: Entry point of the application. Initiates the conversion process.
- `setup.py`: Contains package requirements and installation steps.
- `file_writer.py`: Handles writing FSH files to disk.
- `string_util.py`: Contains utility functions for string manipulation.
- `xlsform_processor.py`: Processes XLSForm files and prepares them for conversion.
- `xlsform_to_fsh_converter.py`: Converts the processed XLSForm data to FSH.

## Dependencies
This script depends Python 3.x and on the following Python modules:
* `re`
* `os`
* `sys`
* `pathlib`
* `shutil`
* `logging`
* `pandas`
* `numpy`
* `openpyxl`
* `traceback`
* `tqdm`

Make sure to have these modules available in your Python environment before running the script.

