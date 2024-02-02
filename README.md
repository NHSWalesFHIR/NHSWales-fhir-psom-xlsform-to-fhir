# XLSForm to FSH to FHIR Converter
This tool facilitates the conversion of `.xlsx` files, compliant with XLSForm standards, into FHIR Shorthand (FSH) format, subsequently enabling their transformation into FHIR resources. The tool specifically accommodates XLSForm files derived from DSCN or LPDS frameworks.

## Usage Instructions
Before running the script, ensure that all necessary dependencies are installed (refer to the dependencies section). Set the paths for `input_folder` and `output_folder` in `main.py` to correspond with your local file system. Executing the `main.py` script initiates the conversion process, wherein each XLSForm file in the input directory is processed and converted into FSH format. The results, along with operation logs, are saved in the output directory.

## Operational Workflow
The script operates using designated `input/` and `output/` directories, executing the following steps:

1. **Output Folder Preparation**: Existing folders in the output directory are cleared and recreated.
2. **XLSForm Processing**: Reads `.xlsx` files from the input directory. These are first converted to XForm for validation, with any issues logged in the output directory.
3. **Detailed Processing per XLSForm**:
   - Extracts critical data such as survey and choices, along with short name, ID, version, and title from the settings tab.
   - Identifies whether the PROMS is DSCN or LPDS based, as indicated by the `lpds_healthboard_abbreviation` key in the settings.
   - Generates FSH for questionnaires and terminology from the extracted data.
   - Saves the FSH output in appropriate subfolders within the output directory, classified into DSCN or Healthboard (LDPS) folders.
   - Logs operational details and errors in `log_file.txt` in the output directory, with errors also echoed to the console.

4. **SUSHI Transformation**: Executes SUSHI to convert FSH files in `/input/fsh/` into FHIR resources within `/fsh-generated/`. This step is performed separately for DSCN and each Healthboard LDPS folder, potentially running multiple times. The generated FHIR resources are then ready for transfer to respective repositories.

## Compatibility with XLSForm Types
This tool supports the conversion of the following XLSForm elements:
* Text
* Select_one
* Decimal
* Integer
* Begin group

Refer to the mapping table provided for details on how specific DSCN fields correspond to XLSForm elements and their subsequent mapping to FHIR resources.

## File Descriptions
- `main.py`: Entry point of the application. Initiates the conversion process.
- `setup.py`: Contains package requirements and installation steps.
- `file_writer.py`: Handles writing FSH lines to disk.
- `string_util.py`: Contains utility functions for string manipulation.
- `xlsform_processor.py`: Processes XLSForm files and prepares them for conversion.
- `xlsform_to_fsh_converter.py`: Converts the processed XLSForm data to FSH lines.

## Dependencies
This script depends on Python 3.x and on the requirements listed in `requirements.txt`.
Make sure to have these modules available in your Python environment before running the script.

## Mapping Table: DSCN/LPDS Fields to XLSForm and FHIR

The table below outlines the mapping from DSCN fields and metadata to corresponding XLSForm fields and their eventual representation in FHIR. Note that some string manipulations may be required to generate the proper FHIR element values, which are not detailed here.

| DSCN/LPDS Field                          | XLSForm Field ([tab] column name)          | FHIR Element(s)          |
| ----------------------------------- | ------------------------ | ------------------------ |
| Full PROMs Tool name (e.g. Your General Health Questionnaire)                | [settings] form_title  | `Questionnaire.title`<br>`ValueSet.title`<br>`CodeSystem.title`<br>`ValueSet.description`<br>`CodeSystem.description` |
| PROMs Tool code (e.g. E5D1)                        | [settings] form_id     | Not used                 |
| PROMs Data Standard Version (e.g. 2022014)            | [settings] version     | `Questionnaire.version`<br>`ValueSet.version`<br>`CodeSystem.version` |
| PROMs Tool Short name  (e.g. EQ5D5L)                            | [settings] tool_short_form | `Questionnaire.id`<br>`Questionnaire.name`<br>`Questionnaire.url`<br>`ValueSet.id`<br>`ValueSet.name`<br>`ValueSet.url`<br>`CodeSystem.id`<br>`CodeSystem.name`<br>`CodeSystem.url`<br>Used for File naming |
| Healthboard Abbreviation (e.g. CAV) to determine if XLSForm is a LPDS             | [settings] lpds_healthboard_abbreviation | `Questionnaire.id`<br>`Questionnaire.name`<br>`Questionnaire.url`<br>`ValueSet.id`<br>`ValueSet.name`<br>`ValueSet.url`<br>`CodeSystem.id`<br>`CodeSystem.name`<br>`CodeSystem.url`<br>Used for Folder naming |
| Format                              | [survey] format        | `Questionnaire.item.extension(url = http://hl7.org/fhir/StructureDefinition/entryFormat)` |
| -                                   | [survey] sensitive     | `Questionnaire.item.extension(url = http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label)` |
| Data Item Name                      | [choices] list_name    | `Questionnaire.item.answerValueSet`<br>`ValueSet.id`<br>`ValueSet.url`<br>`ValueSet.name`<br>`ValueSet.title`<br>`CodeSystem.id`<br>`CodeSystem.url`<br>`CodeSystem.name`<br>`CodeSystem.title` |
| Value Set codes                      | [choices] name         | `ValueSet.include.concept.code`<br>`CodeSystem.concept.code` |
| Value Set label                      | [choices] label        | `ValueSet.include.concept.display`<br>`CodeSystem.concept.display` |
| -                                   | [choices] valid_from   | not implemented          |
| -                                   | [choices] valid_to     | not implemented          |

This extended mapping table serves as a comprehensive guide for transforming DSCN metadata into FHIR-compatible elements through an intermediary XLSForm.
