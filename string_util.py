import re

# Define a function to transform strings
def convert_to_camel_case(s: str) -> str:
    """
    Converts a given string into CamelCase.

    Parameters:
    s (str): The string to be converted. Words should be separated by hyphens.

    Returns:
    str: The converted string in CamelCase.
    
    Examples:
    >>> convert_to_camel_case('hello-world')
    'HelloWorld'

    >>> convert_to_camel_case('this-is-a-test')
    'ThisIsATest'
    """
    s = str(s)
    words = re.split('-|–| ', s)
    words = [word.capitalize() for word in words]
    return ''.join(words)

def pascal_to_readable(s : str) -> str:
    """
    Converts a PascalCased string to a human-readable string.

    Parameters:
    pascal_string (str): A PascalCased string to convert.

    Returns:
    str: A human-readable string.
    """
    if not isinstance(s, str):
        return None
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s).title()

def format_string_case(s: str) -> str:
    """
    This function takes a string as input and returns a new string where the 
    first word is in title case (i.e., the first letter is capitalized and 
    all subsequent letters are in lower case), and all subsequent words are in lower case.

    Args:
    s (str): The input string to be formatted.

    Returns:
    str: The formatted string.
    """
    words = s.split()
    return words[0].capitalize() + ' ' + ' '.join(word.lower() for word in words[1:])

def pascal_to_case(s : str) -> str:
    """
    This function takes a PascalCase string as input and returns a new string where 
    the first word is in title case (i.e., the first letter is capitalized and 
    all subsequent letters are in lower case), and all subsequent words are in lower case.
    
    If the input is not a string, the function returns None.

    Args:
    s (str): The input string to be formatted. It is expected to be in PascalCase.

    Returns:
    str: The formatted string, or None if the input is not a string.
    """
    if not isinstance(s, str):
        return None

    return format_string_case(pascal_to_readable(s))

def pascal_to_snake_upper(s: str) -> str:
    """
    This function takes a PascalCase string as input and returns a new string 
    formatted in snake_case where each word is separated by an underscore, 
    and all letters are in uppercase.

    Args:
    s (str): The input string to be formatted. It is expected to be in PascalCase.

    Returns:
    str: The formatted string in uppercase snake_case.
    """
    if not isinstance(s, str):
        return None

    return ''.join(['_' + i.lower() if i.isupper() else i for i in s]).lstrip('_').upper()

def escape_quotes(s):
    """
    This function checks if the input is a string, and if so, escapes all double quotation marks within it.
    If the input is not a string, it returns the input as it is.

    Parameters:
    s (str): The input which can be of any data type.

    Returns:
    The escaped string if input is a string, else returns the input as is.

    Example:
    --------
    >>> escape_quotes('This "quote" is embedded in a string.')
    'This \\"quote\\" is embedded in a string.'

    >>> escape_quotes(123)
    123
    """
    if isinstance(s, str):
        return s.replace('"', '\\"')
    else:
        return s

def make_fhir_compliant(s: str) -> str:
    """
    This function takes a string as input and returns a new string that is compliant with FHIR id rules.
    FHIR ids only allow ASCII letters (A-Z, a-z), numbers (0-9), hyphens (-), and dots (.), with a length limit of 64 characters.
    In this function, any characters not allowed in a FHIR ID are removed. The function also replaces em-dashes and spaces with no character. 
    Finally, the string is trimmed to a maximum length of 64 characters, if necessary.
    
    Args:
    s (str): The input string to be formatted.

    Returns:
    str: The formatted string that is FHIR id compliant.
    """
    s = re.sub(r'[^A-Za-z0-9.-]', '', s)  # remove disallowed characters
    s = s.replace('–', '')  # replace em-dashes
    s = s.replace(' ', '')  # replace spaces
    return s[:64]  # ensure the string is not longer than 64 characters

def validate_string_FHIR_id(input_string: str) -> bool:
    # Regex pattern for ASCII letters, numbers, hyphen, and dots
    pattern = re.compile(r'^[A-Za-z0-9\-.]+$')
    
    if pattern.fullmatch(input_string):
        return True
    else:
        return False
