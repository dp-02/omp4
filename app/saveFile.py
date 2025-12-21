import os
from dotenv import load_dotenv
import uuid

load_dotenv()
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')

def save(file, file_path):
    '''
    儲存檔案
    '''
    _root, ext = os.path.splitext(file.filename)

    filename = str(uuid.uuid4()) + ext
    father_path = os.path.join(UPLOAD_FOLDER, file_path)
    child_path = os.path.join(file_path, filename)
    
    os.makedirs(father_path, exist_ok=True)
    
    save_path = os.path.join(father_path, filename)
    file.save(save_path)

    print(f'File "{filename}" uploaded successfully!')

    return child_path

def delete_file(file_path):
    '''
    刪除檔案
    '''
    path = os.path.join(UPLOAD_FOLDER, file_path)
    os.remove(path)

    print(f'File "{path}" delete successfully!')
    return