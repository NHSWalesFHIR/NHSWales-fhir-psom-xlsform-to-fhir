from pathlib import Path
from tqdm import tqdm
import logging

def write_fsh_files(fsh_lines_list, output_folder, terminology_folder, questionnaire_folder):
    with tqdm(total=len(fsh_lines_list), desc="Writing FSH to files", dynamic_ncols=True) as pbar:
        for file_name, questionnaire_fsh_lines, questionnaire_terminology_fsh_lines, question_reference_codesystem_fsh_lines, question_reference_valueset_fsh_lines, short_name, version in fsh_lines_list:
            logging.info(f'Saving {file_name}...')
            write_to_file(questionnaire_fsh_lines,                  questionnaire_folder, short_name, output_folder, version )
            write_to_file(questionnaire_terminology_fsh_lines,      terminology_folder,   short_name, output_folder, version )
            write_to_file(question_reference_codesystem_fsh_lines,  terminology_folder,   short_name, output_folder, version )
            write_to_file(question_reference_valueset_fsh_lines,    terminology_folder , 'QuestionReferenceVS', output_folder, '')
            pbar.update(1)
            logging.info(f'Saved {file_name}...')

def write_to_file(lines: list, foldername: str, file_name: str, output_folder: str, version: str) -> None:
    folder = Path(output_folder) / foldername
    folder.mkdir(parents=True, exist_ok=True) 
    filepath = folder / (f"{file_name}-v{version}.fsh")
    
    mode = 'a' if filepath.exists() else 'w'
    with filepath.open(mode, encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n') 

def write_to_md_sorted(entries: list, md_file_path: str) -> None:
    entries.sort(key=lambda x: x['short_name'])
    with open(md_file_path, 'w') as md_file:
        md_file.write("# DSCN PROMs transformation results\n")
        md_file.write("## From XLSForm Spreadsheets to FHIR Resources\n")
        md_file.write("The following is a comprehensive list of the DSCN PROMs that have been processed and transformed into FHIR resources. Each entry specifies the Short Name, Short ID, and Version of the processed XLSForm.\n\n")
        for entry in entries:
            md_file.write(f"- **{entry['short_name']}** ({entry['short_id']}) - {entry['version']}\n")