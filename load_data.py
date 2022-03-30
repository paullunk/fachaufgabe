"""
Cassini Technical Assignment
Paul Lunkenheimer

Function load_data performs following task:
    For the first part of the exercise, we ask you to download (with a script if you can) the complete data from
    www.transtats.bts.gov (https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr)
    for the entire year 2019 and write a script that imports the data into a database with adjustable specifications.
"""

import urllib.request   # Used to download files
import os               # Used to delete zip files
import zipfile          # Used to extract data from zip files
import pandas as pd     # Used as Python Data Analysis Library
import warnings         # Used to supress warnings when importing csv files into pandas

def load_data(url_path, zip_start, zip_it, zip_end):
    """
    Returns pandas.DataFrame containing merged data from given URLs

    Parameter zip_it is list of strings
    Concatenates string parameters url_path, zip_start, zip_it[i] and zip_end to get the i-th URL
    Downloads zip files from all URLs
    Extracts csv files from zip folders
    Imports csv files into pandas
    Concatenates all data into one pandas.DataFrame
    """
    csv_names = []

    # Download zip files, extract csv files, delete zip files
    for i in zip_it:
        zip_name = zip_start + i + zip_end
        url = url_path + zip_name

        print('\nDownload data from: \n\t' + url + '\nThis will take a while!')
        urllib.request.urlretrieve(url, zip_name)
        print('Data saved to: \n\t' + zip_name)

        print('Extract csv files.')
        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            for content_name in zip_ref.namelist():                
                if content_name.endswith('.csv'):
                    zip_ref.extract(content_name)
                    csv_names.append(content_name)
        print('Extraction finished. Delete zip file.')
        os.remove(zip_name)

    # Import csv files into pandas and merge all data
    print('\nImport csv files into pandas.')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pd_db_seperate = [pd.read_csv(csv_name) for csv_name in csv_names]
    pd_db = pd.concat(pd_db_seperate, ignore_index=True)

    return pd_db