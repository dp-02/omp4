from flask import Blueprint, request, make_response, jsonify
from app.database import session_scope
from app.saveFile import save, delete_file
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
from flask import session as flask_session
from types import SimpleNamespace
from app.models import (
    OptionAttachment, 
    OptionAttachmentImage, 
    OptionAttachmentNote,
    OptionAttachmentAnomalyBreaker,
    OptionAttachmentAnomalyDamaged,
    OptionAttachmentAnomalyImage,
    OptionAttachmentAnomalyOptimizer,
    OptionAttachmentAnomalyPosition,
    OptionAttachmentAnomalyReason,
    OptionAttachmentAnomalyState,
)
import json
import re

blueprint = Blueprint('api_attachment', __name__)

@blueprint.route('/save/<table_type>', methods=['POST'])
def save_attachment_image(table_type):
    ''' 儲存附件資料 '''
    response = jsonify({
        "status": "success", 
        "message": "預留位置：邏輯尚未實作"
    })

    with session_scope() as session:
        option_attachment = None
        # 處裡 form 欄位
        
        for key, value in request.form.items():
            parts = key.split('_')
            if len(parts) < 2 : continue

            requset_data = SimpleNamespace()
            requset_data.attachment_type = parts[0]
            requset_data.act = parts[1]
            requset_data.name = parts[2]

            # 處裡 image
            if requset_data.attachment_type == 'image':
                if requset_data.act == 'create':
                    requset_data.option_uid = parts[3]
                    option_attachment = option_attachment if option_attachment else OptionAttachment.create(session, option_uid = requset_data.option_uid, table_type= table_type, type = requset_data.attachment_type)
                    if requset_data.name == "note":
                        OptionAttachmentNote.create(session, option_attachment_uid = option_attachment.uid, value = value)

                elif requset_data.act == 'update':
                    requset_data.attachment_uid = parts[3]
                    if requset_data.name == "note":
                        stmt = select(OptionAttachmentNote).where(OptionAttachmentNote.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: existing.value = value
            # 處裡 anomaly
            elif requset_data.attachment_type == 'anomaly':
                if requset_data.act == 'create':
                    requset_data.option_uid = parts[3]
                    option_attachment = option_attachment if option_attachment else OptionAttachment.create(session, option_uid = requset_data.option_uid, table_type= table_type, type = requset_data.attachment_type)
                    if requset_data.name == "note":
                        OptionAttachmentNote.create(session, option_attachment_uid = option_attachment.uid, value = value)
                    if requset_data.name == "state":
                        OptionAttachmentAnomalyState.create(session, option_attachment_uid = option_attachment.uid, value = value)
                    if requset_data.name in ["inv", "mppt", "string", "panel"]:
                        stmt = select(OptionAttachmentAnomalyPosition).where(OptionAttachmentAnomalyPosition.option_attachment_uid == option_attachment.uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: 
                            if(requset_data.name=="inv"): existing.inv = None if value == '' else value
                            elif(requset_data.name=="mppt"): existing.mppt = None if value == '' else value
                            elif(requset_data.name=="string"): existing.string = None if value == '' else value
                            elif(requset_data.name=="panel"): existing.panel = None if value == '' else value
                        else :
                            if(requset_data.name=="inv"): OptionAttachmentAnomalyPosition.create(session, option_attachment_uid = option_attachment.uid, inv = None if value == '' else value)
                            elif(requset_data.name=="mppt"): OptionAttachmentAnomalyPosition.create(session, option_attachment_uid = option_attachment.uid, mppt = None if value == '' else value)
                            elif(requset_data.name=="string"): OptionAttachmentAnomalyPosition.create(session, option_attachment_uid = option_attachment.uid, string = None if value == '' else value)
                            elif(requset_data.name=="panel"): OptionAttachmentAnomalyPosition.create(session, option_attachment_uid = option_attachment.uid, panel = None if value == '' else value)
                    if requset_data.name == "reason":
                        OptionAttachmentAnomalyReason.create(session, option_attachment_uid = option_attachment.uid, value = value)
                    if requset_data.name == "optimizer":
                        OptionAttachmentAnomalyOptimizer.create(session, option_attachment_uid = option_attachment.uid, value = value)
                    if requset_data.name == "breaker":
                        value = request.form.getlist(key)
                        OptionAttachmentAnomalyBreaker.create(session, option_attachment_uid = option_attachment.uid, option_red = "red" in value, option_black = "black" in value, option_white = "white" in value, option_blue = "blue" in value, option_yellow = "yellow" in value)
                elif requset_data.act == 'update':
                    requset_data.attachment_uid = parts[3]
                    if requset_data.name == "note":
                        stmt = select(OptionAttachmentNote).where(OptionAttachmentNote.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: existing.value = value
                    if requset_data.name == "state":
                        stmt = select(OptionAttachmentAnomalyState).where(OptionAttachmentAnomalyState.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: existing.value = value
                    if requset_data.name in ["inv", "mppt", "string", "panel"]:
                        stmt = select(OptionAttachmentAnomalyPosition).where(OptionAttachmentAnomalyPosition.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: 
                            if(requset_data.name=="inv"): existing.inv = None if value == '' else value
                            elif(requset_data.name=="mppt"): existing.mppt = None if value == '' else value
                            elif(requset_data.name=="string"): existing.string = None if value == '' else value
                            elif(requset_data.name=="panel"): existing.panel = None if value == '' else value
                    if requset_data.name == "reason":
                        stmt = select(OptionAttachmentAnomalyReason).where(OptionAttachmentAnomalyReason.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: existing.value = value
                    if requset_data.name == "optimizer":
                        stmt = select(OptionAttachmentAnomalyOptimizer).where(OptionAttachmentAnomalyOptimizer.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: existing.value = value
                    if requset_data.name == "breaker":
                        value = request.form.getlist(key)
                        stmt = select(OptionAttachmentAnomalyBreaker).where(OptionAttachmentAnomalyBreaker.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if existing: 
                            existing.option_red = "red" in value
                            existing.option_black = "black" in value
                            existing.option_white = "white" in value
                            existing.option_blue = "blue" in value
                            existing.option_yellow = "yellow" in value
                        else:
                            OptionAttachmentAnomalyBreaker.create(session, option_attachment_uid = requset_data.attachment_uid, option_red = "red" in value, option_black = "black" in value, option_white = "white" in value, option_blue = "blue" in value, option_yellow = "yellow" in value)
        # 處裡 files 欄位
        for key in request.files:
            parts = key.split('_')
            if len(parts) < 2 : continue

            requset_data = SimpleNamespace()
            requset_data.attachment_type = parts[0]
            requset_data.act = parts[1]
            requset_data.name = parts[2]
            requset_data.file_list = request.files.getlist(key)

            if requset_data.attachment_type == 'image':
                if requset_data.name == "files":
                    if requset_data.act == 'create':
                        requset_data.option_uid = parts[3]
                        option_attachment = option_attachment if option_attachment else OptionAttachment.create(session, option_uid = requset_data.option_uid, table_type= table_type, type = requset_data.attachment_type)
                        for f in requset_data.file_list:
                            if f.filename:
                                file_path = save(f,"optionAttachment")
                                OptionAttachmentImage.create(session, option_attachment_uid = option_attachment.uid, file_path = file_path)
                    elif requset_data.act == 'append':
                        requset_data.attachment_uid = parts[3]
                        for f in requset_data.file_list:
                            if f.filename:
                                file_path = save(f,"optionAttachment")
                                OptionAttachmentImage.create(session, option_attachment_uid = requset_data.attachment_uid, file_path = file_path)
            elif requset_data.attachment_type == 'anomaly':
                if requset_data.act == 'create':
                    option_attachment = option_attachment if option_attachment else OptionAttachment.create(session, option_uid = requset_data.option_uid, table_type= table_type, type = requset_data.attachment_type)
                    if requset_data.name == "damaged":
                        requset_data.position = parts[3]
                        requset_data.option_uid = parts[4]
                        stmt = select(OptionAttachmentAnomalyDamaged).where(OptionAttachmentAnomalyDamaged.option_attachment_uid == option_attachment.uid)
                        existing = session.execute(stmt).scalar_one_or_none()
                        if not existing: existing = OptionAttachmentAnomalyDamaged.create(session, option_attachment_uid = option_attachment.uid)
                        f = request.files.get(key)
                        if f:
                            file_path = save(f,"optionAttachment")
                            if requset_data.position == "front":existing.file_path_front = file_path
                            elif requset_data.position == "on":existing.file_path_on = file_path
                            elif requset_data.position == "below":existing.file_path_below = file_path
                            elif requset_data.position == "left":existing.file_path_left = file_path
                            elif requset_data.position == "right":existing.file_path_right = file_path
                            elif requset_data.position == "number":existing.file_path_number = file_path
                    if requset_data.name == "files":
                        requset_data.progress_type = parts[3]
                        requset_data.option_uid = parts[4]
                        for f in requset_data.file_list:
                            if f:
                                file_path = save(f,"optionAttachment")
                                OptionAttachmentAnomalyImage.create(session, option_attachment_uid = option_attachment.uid, type = requset_data.progress_type, file_path = file_path)
                elif requset_data.act == 'append':
                    if requset_data.name == "damaged":
                        requset_data.position = parts[3]
                        requset_data.attachment_uid = parts[4]

                        stmt = select(OptionAttachmentAnomalyDamaged).where(OptionAttachmentAnomalyDamaged.option_attachment_uid == requset_data.attachment_uid)
                        existing = session.execute(stmt).scalar_one_or_none()

                        if not existing: existing = OptionAttachmentAnomalyDamaged.create(session, option_attachment_uid = requset_data.attachment_uid)
                        f = request.files.get(key)
                        if f:
                            file_path = save(f,"optionAttachment")
                            if requset_data.position == "front":
                                if existing.file_path_front:delete_file(existing.file_path_front)
                                existing.file_path_front = file_path
                            elif requset_data.position == "on":
                                if existing.file_path_on:delete_file(existing.file_path_on)
                                existing.file_path_on = file_path
                            elif requset_data.position == "below":
                                if existing.file_path_below:delete_file(existing.file_path_below)
                                existing.file_path_below = file_path
                            elif requset_data.position == "left":
                                if existing.file_path_left:delete_file(existing.file_path_left)
                                existing.file_path_left = file_path
                            elif requset_data.position == "right":
                                if existing.file_path_right:delete_file(existing.file_path_right)
                                existing.file_path_right = file_path
                            elif requset_data.position == "number":
                                if existing.file_path_number:delete_file(existing.file_path_number)
                                existing.file_path_number = file_path
                    if requset_data.name == "files":
                        requset_data.progress_type = parts[3]
                        requset_data.attachment_uid = parts[4]
                        f = request.files.getlist(key)
                        for f in requset_data.file_list:
                            if f:
                                file_path = save(f,"optionAttachment")
                                OptionAttachmentAnomalyImage.create(session, option_attachment_uid = requset_data.attachment_uid, type = requset_data.progress_type, file_path = file_path)
                
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
                selectinload(OptionAttachment.images),
                selectinload(OptionAttachment.anomaly_states),
                selectinload(OptionAttachment.anomaly_images),
                selectinload(OptionAttachment.anomaly_positions),
                selectinload(OptionAttachment.anomaly_reasons),
                selectinload(OptionAttachment.anomaly_optimizers),
                selectinload(OptionAttachment.anomaly_breakers),
                selectinload(OptionAttachment.anomaly_damageds)
            )
            .order_by(OptionAttachment.uid.asc())
        )
        results = session.execute(stmt).scalars().all()

        output_data = []

        for record in results:
            # --- 基礎欄位 ---
            description = record.notes[0].value if record.notes else ""
            
            # --- 初始化擴充欄位變數 ---
            state_value = '0' # 預設未處理
            inv, mppt, string, panel = None, None, None, None
            reason_val = ""
            optimizer_val = ""
            breaker_list = []      # 前端 checkbox 需要 array: ['red', 'blue']
            damaged_images = {}    # 六面圖: {'front': url, ...}
            generic_images = []    # Before/After
            
            if record.notes and len(record.notes) > 0: 
                description = record.notes[0].value
            image_list = []
            state_value = None # 預設狀態
            if record.type == 'anomaly':
                # 1. 狀態 (State)
                if record.anomaly_states:
                    state_value = record.anomaly_states[0].value

                # 2. 位置 (Position) - 假設是一對一 (取第一個)
                if record.anomaly_positions:
                    pos = record.anomaly_positions[0]
                    inv, mppt, string, panel = pos.inv, pos.mppt, pos.string, pos.panel

                # 3. 原因 (Reason)
                if record.anomaly_reasons:
                    reason_val = record.anomaly_reasons[0].value # 這裡是存 UID 字串

                # 4. 優化器 (Optimizer)
                if record.anomaly_optimizers:
                    optimizer_val = record.anomaly_optimizers[0].value

                # 5. 斷路器 (Breaker) - 將 Boolean 轉回 List
                if record.anomaly_breakers:
                    b = record.anomaly_breakers[0]
                    if b.option_red: breaker_list.append('red')
                    if b.option_black: breaker_list.append('black')
                    if b.option_white: breaker_list.append('white')
                    if b.option_blue: breaker_list.append('blue')
                    if b.option_yellow: breaker_list.append('yellow')

                # 6. 六面圖 (Damaged) - 將路徑轉為 URL
                if record.anomaly_damageds:
                    d = record.anomaly_damageds[0]
                    # 定義 mapping: {DB欄位: 前端key}
                    mapping = {
                        d.file_path_front: 'front',
                        d.file_path_on: 'on',
                        d.file_path_below: 'below',
                        d.file_path_left: 'left',
                        d.file_path_right: 'right',
                        d.file_path_number: 'number'
                    }
                    for path, key in mapping.items():
                        if path:
                            damaged_images[key] = f"/download/{path}"

                # 7. 一般異常圖 (Before/After)
                for img in record.anomaly_images:
                    file_url = f"/download/{img.file_path}"
                    generic_images.append({
                        "uid": img.uid,
                        "url": file_url,
                        "name": os.path.basename(img.file_path),
                        "category": img.type, # before / after
                        "isDoc": False
                    })
            else:
                for img in record.images:
                    file_url = f"/download/{img.file_path}"
                    image_list.append({"uid": img.uid,"url": file_url,"name": os.path.basename(img.file_path),"isDoc": False})
            
            # 組裝最終物件 (Flattened structure 對應前端 x-model)
            output_data.append({
                "id": record.uid,
                "isSaved": True, # 標記為已存檔
                "type": record.type,
                "note": description,
                "state": state_value,
                "inv": inv,
                "mppt": mppt,
                "string": string,
                "panel": panel,
                "reason": reason_val,
                "optimizer": optimizer_val,
                "breaker": breaker_list,
                "damaged_images": damaged_images,
                "anomaly_images": generic_images,
                "images": image_list
            })
    return jsonify(output_data)


@blueprint.route('/reason/<option_uid>', methods=['GET'])
def get_reason(option_uid):
    '''取得原因'''
    with session_scope() as session:
        ...
    data = [
        {"id": "1", "name": "面板破損"},
        {"id": "2", "name": "支架鏽蝕"},
        {"id": "3", "name": "接頭過熱"},
        {"id": "4", "name": "遮蔭影響"}
    ]
    return jsonify(data)

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
