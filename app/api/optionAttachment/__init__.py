from flask import Blueprint, request, make_response, url_for, render_template, jsonify
from app.database import session_scope
from app.saveFile import save, delete_file
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from collections import defaultdict
import os
from flask import session as flask_session
from app.models import (
    OptionAttachment, 
    OptionAttachmentImage, 
    OptionAttachmentNote
)
import json

blueprint = Blueprint('api_attachment', __name__)

@blueprint.route('/save/image/<table_type>', methods=['POST'])
def save_attachment_image(table_type):
    '''儲存資料 (包含新增紀錄與更新現有紀錄)'''
    response = make_response()
    
    new_records_map = {}
    updates_map = {}
    for key, value in request.form.items():
        parts = key.split('_')
        if key.startswith('desc_') and len(parts) >= 3:
            option_uid = parts[1]
            record_id = parts[2]
            if record_id not in new_records_map:
                new_records_map[record_id] = {'option_uid': option_uid, 'desc': None, 'files': []}
            new_records_map[record_id]['desc'] = value
        elif key.startswith('update_desc_') and len(parts) >= 3:
            db_uid = parts[2] 
            if db_uid not in updates_map:
                updates_map[db_uid] = {'desc': None, 'files': []}
            updates_map[db_uid]['desc'] = value

    for key in request.files:
        clean_key = key.replace('[]', '')
        parts = clean_key.split('_')
        files = request.files.getlist(key)
        if key.startswith('files_') and len(parts) >= 3:
            option_uid = parts[1]
            record_id = parts[2]
            if record_id not in new_records_map:
                new_records_map[record_id] = {'option_uid': option_uid, 'desc': None, 'files': []}
            new_records_map[record_id]['files'].extend(files)
        elif key.startswith('append_files_') and len(parts) >= 3:
            db_uid = parts[2]
            if db_uid not in updates_map:
                updates_map[db_uid] = {'desc': None, 'files': []}
            updates_map[db_uid]['files'].extend(files)
    with session_scope() as session:
        for record_id, data in new_records_map.items():
            if not data['desc'] and not data['files']: continue
            attachment = OptionAttachment.create(session, option_uid=int(data['option_uid']), table_type=table_type, type='image')
            if data['desc'] and data['desc'].strip():
                OptionAttachmentNote.create(session, option_attachment_uid=attachment.uid, value=data['desc'])
            for file_obj in data['files']:
                if file_obj.filename:
                    file_path = save(file_obj, "optionAttachment")
                    if file_path:
                        OptionAttachmentImage.create(session, option_attachment_uid=attachment.uid, file_path=file_path)

        # --- 處理更新 (Update Existing Records) ---
        for db_uid, data in updates_map.items():
            attachment_uid = int(db_uid)
            if data['desc'] is not None:
                stmt = select(OptionAttachmentNote).where(OptionAttachmentNote.option_attachment_uid == attachment_uid)
                existing_note = session.execute(stmt).scalar_one_or_none()
                if existing_note:
                    existing_note.value = data['desc']
                elif data['desc'].strip():
                    OptionAttachmentNote.create(session, option_attachment_uid=attachment_uid, value=data['desc'])
            for file_obj in data['files']:
                if file_obj.filename:
                    file_path = save(file_obj, "optionAttachment")
                    if file_path:
                        OptionAttachmentImage.create(
                            session, 
                            option_attachment_uid=attachment_uid, 
                            file_path=file_path
                        )
    response.headers['HX-Trigger'] = json.dumps({
        "response-data": {
            "title": "資料儲存成功！"
        }
    })
    return response


@blueprint.route('/get_saved/image/<table_type>/<option_uid>', methods=['GET'])
def get_saved_image(table_type, option_uid):
    '''讀取資料'''
    with session_scope() as session:
        stmt = (
            select(OptionAttachment)
            .where(
                OptionAttachment.option_uid == int(option_uid),
                OptionAttachment.table_type == table_type 
            )
            .options(
                selectinload(OptionAttachment.notes),
                selectinload(OptionAttachment.images)
            )
            .order_by(OptionAttachment.uid.asc())
        )
        results = session.execute(stmt).scalars().all()

        output_data = []

        for record in results:
            description = ""
            if record.notes and len(record.notes) > 0: description = record.notes[0].value
            image_list = []
            for img in record.images:
                file_url = f"/download/{img.file_path}"
                image_list.append({
                    "uid": img.uid,
                    "url": file_url,
                    "name": os.path.basename(img.file_path)
                })
            output_data.append({
                "id": record.uid,
                "type": record.type,
                "desc": description,
                "images": image_list
            })
    return jsonify(output_data)

@blueprint.route('/delete/<int:uid>', methods=['DELETE'])
def delete_option_attachment(uid):
    with session_scope() as session:
        stmt = select(OptionAttachment).where(OptionAttachment.uid == uid)
        attachment = session.execute(stmt).scalar_one_or_none()
        if not attachment:
            return jsonify({'error': 'Record not found'}), 404
        if attachment.images:
            for img in attachment.images:
                delete_file(img.file_path)
        OptionAttachment.delete(session, uid = uid)            
    return jsonify({'message': 'Record deleted successfully'}), 200

@blueprint.route('/image/delete/<int:image_uid>', methods=['DELETE'])
def delete_attachment_single_image(image_uid):
    with session_scope() as session:
        stmt = select(OptionAttachmentImage).where(OptionAttachmentImage.uid == image_uid)
        image_record = session.execute(stmt).scalar_one_or_none()
        if not image_record:
            return jsonify({'error': 'Image not found'}), 404
        delete_file(image_record.file_path)
        OptionAttachmentImage.delete(session, uid = image_uid)
    return jsonify({'message': 'Image deleted successfully'}), 200