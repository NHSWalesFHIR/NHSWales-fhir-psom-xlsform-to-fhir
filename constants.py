"""
Constants used across the FSH generation process.
"""
# FHIR Status
FHIR_STATUS_DRAFT = "#draft"

# Common Prefixes
LPDS_PREFIX = "LPDS"
DSCN_PREFIX = "DataStandardsWales"

# URLs
QUESTION_REFERENCE_CS_URL_DSCN = "https://fhir.nhs.wales/CodeSystem/QuestionReferenceCS"
QUESTION_REFERENCE_CS_URL_LPDS = "https://fhir.nhs.wales/CodeSystem/LPDSQuestionReferenceCS"
NHS_WALES_BASE_URL = "https://fhir.nhs.wales"

# Extension URLs
ENTRY_FORMAT_EXTENSION_URL = "http://hl7.org/fhir/StructureDefinition/entryFormat"
SECURITY_LABEL_EXTENSION_URL = "http://hl7.org/fhir/uv/security-label-ds4p/StructureDefinition/extension-inline-sec-label"
SECURITY_LABEL_CODING_URL = "http://terminology.hl7.org/CodeSystem/v3-ActCode#PDS"

# Publishers
NHS_WALES_PUBLISHER = "NHS Wales"

# Copyright messages
COPYRIGHT_QUESTIONNAIRE_LPDS = "The information provided in this Questionnaire may not be used to re-produce a PROM questionnaire form, this may result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
COPYRIGHT_QUESTIONNAIRE_DSCN = "The information provided in this Questionnaire must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."

COPYRIGHT_CS_LPDS = "The information provided in the CodeSystem may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
COPYRIGHT_VS_LPDS = "The information provided in the ValueSet may be part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
COPYRIGHT_CS_DSCN = "The information provided in the CodeSystem is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."
COPYRIGHT_VS_DSCN = "The information provided in the ValueSet is part of a licensed PROM questionnaire form. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."

COPYRIGHT_QUESTION_REFERENCE_DSCN = "The information provided in this CodeSystem must not be used to re-produce a PROM questionnaire form, this would result in a breach of copyright. The user must ensure they comply with the terms of the license set by the license holder for any PROM questionnaires used."