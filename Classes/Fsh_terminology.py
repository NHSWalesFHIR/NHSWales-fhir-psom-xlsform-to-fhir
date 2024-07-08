import string_util as su
import terminology_util as tu
from Classes.XLS_Form import XLS_Form

class Fsh_terminology:

    copyright_cs_lpds = "The information provided in the CodeSystem may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
    copyright_vs_lpds = "The information provided in the ValueSet may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
    copyright_cs = "The information provided in the CodeSystem is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
    copyright_vs = "The information provided in the ValueSet is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."

    def __init__(self, data: XLS_Form):
        """
        FSH representation of terminology systems. Transforms an XLSForm into FSH CodeSystems and FSH ValueSets.

        Args:
            data (XlsFormData): The data from an XLSForm.
        """

        self.data = data
        self.lines = []

        for list_name in data.df_choices['list_name'].unique():
            proper_list_name = su.convert_to_camel_case(list_name)
                
            cs_id = tu.generate_vs_or_cs_id(data.short_name, list_name, 'CS', data.lpds_healthboard_abbreviation)
            vs_id = tu.generate_vs_or_cs_id(data.short_name, list_name, 'VS', data.lpds_healthboard_abbreviation)

            self.fill_cs_or_vs(cs_id, list_name, proper_list_name, "")
            self.fill_cs_or_vs(vs_id, list_name, proper_list_name, cs_id)
    
    def fill_cs_or_vs(self, id: str, list_name:str, proper_list_name: str, cs_id: str) -> None:

        if cs_id != "":
            name_addition = "VS"
            copyright = self.copyright_vs
        else :
            name_addition = "CS"
            copyright = self.copyright_cs

        publisher = "NHS Wales"

        name = ""

        if self.data.lpds_healthboard_abbreviation:
            publisher = self.data.lpds_healthboard_abbreviation.replace('-', '')

            name = self.data.lpds_healthboard_abbreviation

            if cs_id != "":
                copyright = self.copyright_vs_lpds
            else:
                copyright = self.copyright_cs_lpds

        processed_name = (name + self.data.short_name + proper_list_name + name_addition).replace('-', '_')

        selector = lambda x: "ValueSet" if x != "" else "CodeSystem"

        vs_or_cs_lines = [
            f"{selector(cs_id)}: {id}",
            f"Id: {id}",
            f'Title: "{self.data.short_name} Questionnaire - {proper_list_name} {selector(cs_id)}"',
            f'Description: "Codes for the question \'{proper_list_name}\' in PSOM Questionnaire \'{self.data.title}\'."',
            f'* ^name = "{processed_name}"',
            f'* ^version = "{self.data.version}"',
            f'* ^status = #draft',
            f'* ^copyright = "{copyright}"',
            f'* ^publisher = "{publisher}"',
            ]
        
        if not cs_id != "":
            vs_or_cs_lines.append('* ^caseSensitive = true')
            
        vs_or_cs_lines.append('')

        for _, row in self.data.df_choices[self.data.df_choices['list_name'] == list_name].iterrows():
            code = f'* {cs_id}#{row["name"]} "{su.escape_quotes(row["label"])}"'
            vs_or_cs_lines.append(code)

        self.lines.extend(vs_or_cs_lines)
        self.lines.append('')

    


    