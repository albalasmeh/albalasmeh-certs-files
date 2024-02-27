import os
import glob
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import time

# Your Google API key credentials JSON file
SERVICE_ACCOUNT_FILE = 'service_account_key.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    return service

def create_folder(service, name, parent_folder_id):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

def upload_file(service, file_path, parent_folder_id):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [parent_folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def upload_to_drive(parent_folder_id):
    service = get_drive_service()

    # Create a new folder inside the parent folder with today's date
    today = time.strftime('%Y-%m-%d')
    new_folder_name = f'Certificates-{today}'
    new_folder_id = create_folder(service, new_folder_name, parent_folder_id)

    # Upload all PDF files in the 'out' directory to the newly created folder
    uploaded_count = 0
    start_time = time.time()

    for file_path in glob.glob('out/*.pdf'):
        upload_file(service, file_path, new_folder_id)
        uploaded_count += 1

    elapsed_time = time.time() - start_time
    return uploaded_count, elapsed_time

def main():
    PARENT_FOLDER_ID = '14uCMIIE2J1QPKVaVLDxmm76g_WYm2LrR'
    uploaded_count, elapsed_time = upload_to_drive(PARENT_FOLDER_ID)

    # Create a JSON output for the uploaded_count and elapsed_time
    result = {"uploaded_count": uploaded_count, "elapsed_time": elapsed_time}
    print(json.dumps(result))

if __name__ == "__main__":
    main()



"""
import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SERVICE_ACCOUNT_FILE = 'service_account_key.json'

def create_folder(drive_service, folder_name, parent_id=None):
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    if parent_id:
        folder_metadata['parents'] = [parent_id]

    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def upload_files(drive_service, folder_id, local_folder_path):
    for file_name in os.listdir(local_folder_path):
        local_file_path = os.path.join(local_folder_path, file_name)
        if os.path.isfile(local_file_path):
            media = MediaFileUpload(local_file_path, resumable=True)
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f'Uploaded "{file_name}" to the folder.')

def main():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive']
    )

    drive_service = build('drive', 'v3', credentials=credentials)

    # Replace this with the ID of the folder in Google Drive where you want to upload the files.
    parent_folder_id = '1EWd31A7MckA1g4esJL0hrMzzeKrWxhT7'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    new_folder_name = f'Certificates-{today}'
    new_folder_id = create_folder(drive_service, new_folder_name, parent_folder_id)

    local_folder_path = 'out'
    upload_files(drive_service, new_folder_id, local_folder_path)

if __name__ == '__main__':
    main()
"""
