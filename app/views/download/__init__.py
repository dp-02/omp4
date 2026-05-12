from flask import Blueprint, send_from_directory
from app.auth import user_or_guest_required
import os
from dotenv import load_dotenv
load_dotenv()
blueprint = Blueprint('view_download', __name__)

@blueprint.route('/<path:filename>')
@user_or_guest_required
def download(filename):
    '''
    ### 下載
    '''
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
    file_path = os.path.join('../',UPLOAD_FOLDER)
    return send_from_directory(
        file_path,
        filename,
        # as_attachment=True
    )

@blueprint.route('/attachment/<path:filename>')
@user_or_guest_required
def attachment(filename):
    '''
    ### 下載
    '''
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
    file_path = os.path.join('../',UPLOAD_FOLDER)
    return send_from_directory(
        file_path,
        filename,
        as_attachment=True
    )