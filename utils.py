import os
import time
import csv
import json
from io import StringIO

import dropbox

TOKEN = os.environ.get('DROPBOX_TOKEN')
FOLDER = os.environ.get('DROPBOX_PATH')

dbx = dropbox.Dropbox(TOKEN)


def get_monefy_info():

    file_names = [entry.name for entry in dbx.files_list_folder(FOLDER).entries
                  if entry.name.endswith('.csv')]

    monefy_csv_backup_file = {}

    for file_name in file_names:
        metadata, response = dbx.files_download(FOLDER + file_name)
        print(metadata)
        data = response.content
        data_content = data.decode(encoding='utf-8-sig')
        data_as_file = StringIO(data_content)
        csv_data = csv.DictReader(data_as_file)
        monefy_file = []
        for transaction in csv_data:
            monefy_file.append(transaction)
        monefy_csv_backup_file[file_name] = monefy_file

    return json.dumps(monefy_csv_backup_file)


def write_monefy_info():

    file_names = [entry.name for entry in dbx.files_list_folder(FOLDER).entries
                  if entry.name.endswith('.csv')]

    for file_name in file_names:
        with open(f'monefy_{time.strftime("%Y%m%d-%H%M%S")}.csv', 'wb') as f:
            metadata, response = dbx.files_download(FOLDER + file_name)
            print(metadata)
            print(response)
            f.write(response.content)
    return 'done'


if __name__ == '__main__':
    get_monefy_info()
