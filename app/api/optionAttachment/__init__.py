from flask import Blueprint, request, make_response, jsonify
from app.database import session_scope
from app.saveFile import save, delete_file
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
from flask import session as flask_session
from app.models import (
    OptionAttachment, 
    OptionAttachmentImage, 
    OptionAttachmentNote,
    OptionAttachmentAnomalyState,
    OptionAttachmentAnomalyImage
)
import json

blueprint = Blueprint('api_attachment', __name__)

@blueprint.route('/save/image/<table_type>', methods=['POST'])
def save_attachment_image(table_type):
    '''儲存圖片資料 (僅處理一般圖片，自動忽略異常紀錄的 before/after 圖片)'''
    response = make_response()
    
    new_records_map = {}
    updates_map = {}
    
    for key, value in request.form.items():
        parts = key.split('_')
        if 'anomaly' in key: continue

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
        if 'before' in parts or 'after' in parts:
            continue

        if key.startswith('files_') and len(parts) >= 3:
            option_uid = parts[1]
            record_id = parts[2]
            
            if not option_uid.isdigit(): continue

            if record_id not in new_records_map:
                new_records_map[record_id] = {'option_uid': option_uid, 'desc': None, 'files': []}
            new_records_map[record_id]['files'].extend(files)

        elif key.startswith('append_files_') and len(parts) >= 3:
            db_uid = parts[2]
            if not db_uid.isdigit(): continue
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
                        OptionAttachmentImage.create(session, option_attachment_uid=attachment_uid, file_path=file_path)
    response.headers['HX-Trigger'] = json.dumps({
        "response-data": {
            "title": "資料儲存成功！"
        }
    })
    return response
@blueprint.route('/save/anomaly/<table_type>', methods=['POST'])
def save_attachment_anomaly(table_type):
    '''儲存異常紀錄 (包含新增紀錄與更新現有紀錄)'''
    response = make_response()
    new_records_map = {} # 格式: { 'temp_id': { option_uid, status, desc, files: [{obj, type}] } }
    updates_map = {}     # 格式: { 'db_uid': { status, desc, files: [{obj, type}] } }

    for key, value in request.form.items():
        parts = key.split('_')
        if key.startswith('desc_') or key.startswith('update_desc_'):
            continue

        if key.startswith('anomaly_status_'):
            if len(parts) >= 4: # 新增
                option_uid = parts[2]
                record_id = parts[3]
                if record_id not in new_records_map:
                    new_records_map[record_id] = {'option_uid': option_uid, 'status': None, 'desc': None, 'files': []}
                new_records_map[record_id]['status'] = value
            elif len(parts) == 3: # 更新
                db_uid = parts[2]
                if db_uid not in updates_map:
                    updates_map[db_uid] = {'status': None, 'desc': None, 'files': []}
                updates_map[db_uid]['status'] = value
        elif key.startswith('anomaly_desc_') and len(parts) >= 4:
            option_uid = parts[2]
            record_id = parts[3]
            if record_id not in new_records_map:
                new_records_map[record_id] = {'option_uid': option_uid, 'status': None, 'desc': None, 'files': []}
            new_records_map[record_id]['desc'] = value
        elif key.startswith('update_anomaly_desc_') and len(parts) >= 4:
            db_uid = parts[3] 
            if db_uid not in updates_map:
                updates_map[db_uid] = {'status': None, 'desc': None, 'files': []}
            updates_map[db_uid]['desc'] = value

    for key in request.files:
        clean_key = key.replace('[]', '')
        parts = clean_key.split('_')
        file_list = request.files.getlist(key)
        if 'before' not in parts and 'after' not in parts:
            continue
        img_type = 'before' # 預設為 before
        if '_after_' in key:
            img_type = 'after'
        if key.startswith('files_') and len(parts) >= 4:
            option_uid = parts[2]
            record_id = parts[3]
            if record_id not in new_records_map:
                new_records_map[record_id] = {'option_uid': option_uid, 'status': None, 'desc': None, 'files': []}
            for f in file_list:
                new_records_map[record_id]['files'].append({'obj': f, 'type': img_type})
        elif key.startswith('append_files_') and len(parts) >= 4:
            db_uid = parts[3]
            if db_uid not in updates_map:
                updates_map[db_uid] = {'status': None, 'desc': None, 'files': []}
            for f in file_list:
                updates_map[db_uid]['files'].append({'obj': f, 'type': img_type})
    with session_scope() as session:
        
        # --- A. 處理新增 (New Records) ---
        for record_id, data in new_records_map.items():
            attachment = OptionAttachment.create(session, option_uid=int(data['option_uid']), table_type=table_type, type='anomaly')
            if data['status'] is not None:
                OptionAttachmentAnomalyState.create(session, option_attachment_uid=attachment.uid, value=data['status'])
            if data['desc'] and data['desc'].strip():
                OptionAttachmentNote.create(session, option_attachment_uid=attachment.uid, value=data['desc'])
            for file_info in data['files']:
                file_obj = file_info['obj']
                category_type = file_info['type'] # 'before' or 'after'
                if file_obj.filename:
                    file_path = save(file_obj, "optionAttachment/anomaly")
                    if file_path:
                        OptionAttachmentAnomalyImage.create(session, option_attachment_uid=attachment.uid, file_path=file_path,type=category_type)
        for db_uid, data in updates_map.items():
            attachment_uid = int(db_uid)
            if data['status'] is not None:
                stmt = select(OptionAttachmentAnomalyState).where(OptionAttachmentAnomalyState.option_attachment_uid == attachment_uid)
                existing_state = session.execute(stmt).scalar_one_or_none()
                if existing_state:
                    existing_state.value = data['status']
                else:
                    OptionAttachmentAnomalyState.create(session, option_attachment_uid=attachment_uid, value=data['status'])
            if data['desc'] is not None:
                stmt = select(OptionAttachmentNote).where(OptionAttachmentNote.option_attachment_uid == attachment_uid)
                existing_note = session.execute(stmt).scalar_one_or_none()
                
                if existing_note:
                    existing_note.value = data['desc']
                elif data['desc'].strip():
                    OptionAttachmentNote.create(session, option_attachment_uid=attachment_uid, value=data['desc'])
            for file_info in data['files']:
                file_obj = file_info['obj']
                category_type = file_info['type']
                if file_obj.filename:
                    file_path = save(file_obj, "optionAttachment/anomaly")
                    if file_path:
                        OptionAttachmentAnomalyImage.create(session, option_attachment_uid=attachment_uid, file_path=file_path,type=category_type)
    # HTMX Trigger 回傳
    response.headers['HX-Trigger'] = json.dumps({
        "reload-attachments": True,
        "response-data": {
            "title": "異常紀錄儲存成功！"
        }
    })
    return response

@blueprint.route('/get_saved/<table_type>/<option_uid>', methods=['GET'])
def get_saved(table_type, option_uid):
    '''讀取所有附件資料'''
    with session_scope() as session:
        stmt = (
            select(OptionAttachment)
            .where(
                OptionAttachment.option_uid == int(option_uid),
                OptionAttachment.table_type == table_type 
            )
            .options(
                selectinload(OptionAttachment.notes),
                selectinload(OptionAttachment.images),          # 一般圖片
                selectinload(OptionAttachment.anomaly_states),  # [新增] 異常狀態
                selectinload(OptionAttachment.anomaly_images)   # [新增] 異常照片
            )
            .order_by(OptionAttachment.uid.asc())
        )
        results = session.execute(stmt).scalars().all()

        output_data = []

        for record in results:
            description = ""
            if record.notes and len(record.notes) > 0: 
                description = record.notes[0].value
            image_list = []
            status_value = None # 預設狀態
            if record.type == 'anomaly':
                # A. 取得處理進度 (0:未處理, 1:已處理, 2:不可處理)
                if record.anomaly_states and len(record.anomaly_states) > 0:
                    status_value = record.anomaly_states[0].value
                else:
                    status_value = '0' # 若無資料預設為未處理
                # B. 取得異常照片 (區分 before/after)
                for img in record.anomaly_images:
                    file_url = f"/download/{img.file_path}"
                    image_list.append({
                        "uid": img.uid,
                        "url": file_url,
                        "name": os.path.basename(img.file_path),
                        "category": img.type,  # 關鍵：將 DB 的 type 映射給前端的 category
                        "isDoc": False         # 假設都是圖片
                    })
            else:
                for img in record.images:
                    file_url = f"/download/{img.file_path}"
                    image_list.append({
                        "uid": img.uid,
                        "url": file_url,
                        "name": os.path.basename(img.file_path),
                        "isDoc": False
                    })
            output_data.append({
                "id": record.uid,
                "type": record.type,       # 'image' or 'anomaly'
                "desc": description,
                "status": status_value,    # [新增] 給前端 radio button 使用
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


@blueprint.route('/anomaly_image/delete/<int:image_uid>', methods=['DELETE'])
def delete_attachment_anomaly_image(image_uid):
    with session_scope() as session:
        stmt = select(OptionAttachmentAnomalyImage).where(OptionAttachmentAnomalyImage.uid == image_uid)
        image_record = session.execute(stmt).scalar_one_or_none()
        if not image_record:
            return jsonify({'error': 'Image not found'}), 404
        delete_file(image_record.file_path)
        OptionAttachmentAnomalyImage.delete(session, uid = image_uid)
    return jsonify({'message': 'Image deleted successfully'}), 200