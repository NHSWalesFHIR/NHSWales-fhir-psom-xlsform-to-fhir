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

See the mapping table below to know what which DSCN fields should applied to the XLSFrom and how the are mapped to FHIR.

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

## Mapping Table: DSCN Fields to XLSForm and FHIR

The table below outlines the mapping from DSCN fields and metadata to corresponding XLSForm fields and their eventual representation in FHIR. Note that some string manipulations may be required to generate the proper FHIR element values, which are not detailed here.

| DSCN Field                          | XLSForm Field            | FHIR Element(s)          |
| ----------------------------------- | ------------------------ | ------------------------ |
| Full PROMs Tool name                | [settings] form_title  | `Questionnaire.title`<br>`ValueSet.title`<br>`CodeSystem.title`<br>`ValueSet.description`<br>`CodeSystem.description` |
| PROMs Tool code                     | [settings] form_id     | Not used                 |
| PROMs Data Standard Version         | [settings] version     | `Questionnaire.version`<br>`ValueSet.version`<br>`CodeSystem.version` |
| Short name                          | [settings] tool_short_form | `Questionnaire.id`<br>`Questionnaire.name`<br>`Questionnaire.url`<br>`ValueSet.id`<br>`ValueSet.name`<br>`ValueSet.url`<br>`CodeSystem.id`<br>`CodeSystem.name`<br>`CodeSystem.url`<br>Used for File naming |
| Format                              | [survey] format        | `Questionnaire.item.extension(url = http://hl7.org/fhir/StructureDefinition/entryFormat)` |
| -                                   | [survey] sensitive     | `Questionnaire.item.extension(url = http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label)` |
| Data Item Name                      | [choices] list_name    | `Questionnaire.item.answerValueSet`<br>`ValueSet.id`<br>`ValueSet.url`<br>`ValueSet.name`<br>`ValueSet.title`<br>`CodeSystem.id`<br>`CodeSystem.url`<br>`CodeSystem.name`<br>`CodeSystem.title` |
| Value Set codes                      | [choices] name         | `ValueSet.include.concept.code`<br>`CodeSystem.concept.code` |
| Value Set label                      | [choices] label        | `ValueSet.include.concept.display`<br>`CodeSystem.concept.display` |
| -                                   | [choices] valid_from   | not implemented          |
| -                                   | [choices] valid_to     | not implemented          |

This extended mapping table serves as a comprehensive guide for transforming DSCN metadata into FHIR-compatible elements through an intermediary XLSForm.
