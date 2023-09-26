import logging, os, glob, shutil
import logging
import pandas as pd
from openpyxl import load_workbook

def initiate_logging(output_folder):
    """ 
    Sets up logging by creating the output folder if it doesn't exist, 
    removing any previous log file, and configuring the logging settings.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    print('Removing previous log file...')
    log_file = os.path.join(output_folder, 'log_file.txt')

    if os.path.exists(log_file):
        os.remove(log_file)

    # Remove all handlers associated with the root logger object
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure logging to write only to the file
    logging.basicConfig(filename=log_file, level=logging.INFO, filemode='w', format='%(asctime)s ; %(levelname)s; %(message)s')
    logging.info('Logging initiated')  # Test message

def delete_output_folder_contents(output_folder):
    """ 
    Deletes the contents of the entire output folder specified by the given path.

    :param output_folder_path: The path to the output folder whose contents will be deleted.

    This function iterates through all files and subdirectories in the specified folder and deletes them.
    If the folder does not exist, a warning message will be printed.
    """
    if os.path.exists(output_folder):
        files = glob.glob(output_folder + '*')
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
            elif os.path.isdir(f):
                shutil.rmtree(f)
        print(f"Deleted the contents of the output folder: {output_folder}")
        logging.info(f"Deleted the contents of the output folder: {output_folder}")
    else:
        print(f"Output folder {output_folder} not found!")
        logging.warning(f"Output folder {output_folder} not found!")
