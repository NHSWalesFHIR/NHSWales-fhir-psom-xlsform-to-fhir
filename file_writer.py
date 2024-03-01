from pathlib import Path
from tqdm import tqdm
import logging

def write_fsh_files(fsh_lines_list, output_folder, lpds_healthboard_abbreviation_dict):
    with tqdm(total=len(fsh_lines_list), desc="Writing FSH to files", dynamic_ncols=True) as pbar:
        # Track if the DSCN sushi-config.yaml file has been created
        dscn_sushi_created = False

        for file_name, questionnaire_fsh_lines, questionnaire_terminology_fsh_lines, short_name, version, lpds_healthboard_abbreviation, question_reference_codesystem_fsh_lines in fsh_lines_list:
            logging.info(f'Saving {file_name}...')

            # Determine the base folder
            if lpds_healthboard_abbreviation:
                # LPDS folder structure
                base_folder = Path(output_folder) / "LPDS" / lpds_healthboard_abbreviation / "input" / "fsh"
                canonical_url = lpds_healthboard_abbreviation_dict.get(lpds_healthboard_abbreviation, "https://fhir.nhs.wales")
            else:
                # DSCN folder structure
                base_folder = Path(output_folder) / "DSCN" / "input" / "fsh"
                canonical_url = "https://fhir.nhs.wales"

            # Define questionnaire and terminology folders
            questionnaire_folder = base_folder / "questionnaires"
            terminology_folder = base_folder / "terminology"

            # Create folders if they don't exist
            questionnaire_folder.mkdir(parents=True, exist_ok=True)
            terminology_folder.mkdir(parents=True, exist_ok=True)

            # Write files
            write_to_file(questionnaire_fsh_lines, questionnaire_folder, short_name, version)
            write_to_file(questionnaire_terminology_fsh_lines, terminology_folder, short_name, version)
            write_to_file(question_reference_codesystem_fsh_lines, terminology_folder, short_name, version)

            # Create sushi-config.yaml file for LPDS healthboard or DSCN if not yet created
            if lpds_healthboard_abbreviation or not dscn_sushi_created:
                sushi_config_path = base_folder.parent.parent / "sushi-config.yaml"
                sushi_config_content = f"canonical: {canonical_url}\nfhirVersion: 4.0.1\nversion: 0.1.0\nFSHOnly: true"
                with sushi_config_path.open('w', encoding='utf-8') as sushi_file:
                    sushi_file.write(sushi_config_content)

                if not lpds_healthboard_abbreviation:
                    dscn_sushi_created = True

            pbar.update(1)
            logging.info(f'Saved {file_name}...')

def write_to_file(lines: list, folder: Path, file_name: str, version: str) -> None:
    filepath = folder / (f"{file_name}-v{version}.fsh")
    
    mode = 'a' if filepath.exists() else 'w'
    with filepath.open(mode, encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n') 

def write_to_md_file(md_lines: str, md_file_path: str) -> None:
    with open(md_file_path, 'w') as md_file:
        md_file.write(md_lines)