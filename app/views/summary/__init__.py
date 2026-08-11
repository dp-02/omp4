from flask import Blueprint, render_template, request, jsonify
from app.auth import login_required
from app.database import session_scope
from app.models import (
    Checklist, 
    ChecklistTableOptionData,
    Site,
    ChecklistTableOption,
    OptionAttachment,
    OptionAttachmentForChecklist,
    OptionAttachmentAnomalyReasonSetting
)
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import date

blueprint = Blueprint('view_summary', __name__)

@blueprint.route('/')
@login_required
def index():
    ''' 統整頁面 '''
    return render_template('summary/index.html')

@blueprint.route('/query')
@login_required
def query():
    ''' 統整查詢 API '''
    year_str = request.args.get('year', '2026')
    try:
        year = int(year_str)
    except ValueError:
        year = 2026

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # 各設備統計的 option_uid 清單
    categories = {
        "module": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19],
        "support": [16, 17, 18],
        "inverter": [20, 21, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 118],
        "dc_box": [30, 31, 32, 33, 34, 36, 40, 43],
        "ac_box": [44, 45, 46, 47, 48, 50, 55, 56],
        "meter_box": [88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 105],
        "dc_line": [22, 23, 24, 25, 26, 27, 28, 35, 37, 38, 39, 41, 42],
        "ac_line": [22, 23, 24, 25, 26, 27, 28, 29, 49, 51, 52, 53, 54],
        "transformer": [57, 58, 59, 60],
        "booster": [],
        "monitor": [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87],
        "other": [102, 103, 104, 117],
        "building": [1, 2, 3]
    }

    with session_scope() as session:
        # 1. 取得該年份的 checklist 數量 (分母基數)
        stmt_checklist_count = select(func.count(Checklist.uid)).where(
            Checklist.check_date.between(start_date, end_date)
        )
        checklist_count = session.scalar(stmt_checklist_count) or 0

        # 2. 迴圈統計各項目的資料筆數 (分子)
        results = {}
        for key, uids in categories.items():
            if not uids:
                results[key] = {
                    "count": 0,
                    "percentage": 0.0
                }
                continue

            stmt_count = select(func.count(OptionAttachment.uid))\
                .join(OptionAttachmentForChecklist, OptionAttachmentForChecklist.option_attachment_uid == OptionAttachment.uid)\
                .join(Checklist, OptionAttachmentForChecklist.checklist_uid == Checklist.uid)\
                .where(
                    and_(
                        OptionAttachment.option_uid.in_(uids),
                        OptionAttachment.type == 'anomaly',
                        OptionAttachment.table_type == 'checklist',
                        Checklist.check_date.between(start_date, end_date)
                    )
                )
            count = session.scalar(stmt_count) or 0

            # 百分比的分母是 checklist 數量 * 需統計的 option_uid 數量
            denominator = checklist_count * len(uids)
            percentage = 0.0
            if denominator > 0:
                percentage = (count / denominator) * 100.0

            results[key] = {
                "count": count,
                "percentage": round(percentage, 2)
            }

    return jsonify(results)

@blueprint.route('/detail')
@login_required
def detail():
    ''' 異常明細查詢 API '''
    year_str = request.args.get('year', '2026')
    category = request.args.get('category', 'module')
    try:
        year = int(year_str)
    except ValueError:
        year = 2026

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    categories = {
        "module": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19],
        "support": [16, 17, 18],
        "inverter": [20, 21, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 118],
        "dc_box": [30, 31, 32, 33, 34, 36, 40, 43],
        "ac_box": [44, 45, 46, 47, 48, 50, 55, 56],
        "meter_box": [88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 105],
        "dc_line": [22, 23, 24, 25, 26, 27, 28, 35, 37, 38, 39, 41, 42],
        "ac_line": [22, 23, 24, 25, 26, 27, 28, 29, 49, 51, 52, 53, 54],
        "transformer": [57, 58, 59, 60],
        "booster": [],
        "monitor": [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87],
        "other": [102, 103, 104, 117],
        "building": [1, 2, 3]
    }

    uids = categories.get(category, [])
    if not uids:
        return jsonify([])

    with session_scope() as session:
        # 1. 查詢符合條件的 OptionAttachment 以及相關關聯表
        stmt = select(
            OptionAttachment,
            OptionAttachmentForChecklist.checklist_uid,
            Site.name.label('site_name'),
            ChecklistTableOption.name.label('option_name'),
            ChecklistTableOption.table_uid.label('table_uid'),
            ChecklistTableOption.sort.label('option_sort'),
            Checklist.check_type.label('check_type'),
            Checklist.site_uid.label('site_uid')
        ).options(
            selectinload(OptionAttachment.anomaly_reasons),
            selectinload(OptionAttachment.anomaly_positions),
            selectinload(OptionAttachment.notes)
        ).join(
            OptionAttachmentForChecklist, OptionAttachmentForChecklist.option_attachment_uid == OptionAttachment.uid
        ).join(
            Checklist, OptionAttachmentForChecklist.checklist_uid == Checklist.uid
        ).join(
            Site, Checklist.site_uid == Site.uid
        ).join(
            ChecklistTableOption, OptionAttachment.option_uid == ChecklistTableOption.uid
        ).where(
            and_(
                OptionAttachment.option_uid.in_(uids),
                OptionAttachment.type == 'anomaly',
                OptionAttachment.table_type == 'checklist',
                Checklist.check_date.between(start_date, end_date)
            )
        ).order_by(Checklist.check_date.desc())

        rows = session.execute(stmt).all()

        output = []
        for att, checklist_uid, site_name, option_name, table_uid, option_sort, check_type, site_uid in rows:
            reasons_list = []
            positions_list = []
            notes_list = []
            
            if att.anomaly_reasons:
                for r_item in att.anomaly_reasons:
                    reason_val_str = r_item.value
                    if reason_val_str:
                        try:
                            reason_val_int = int(reason_val_str)
                            stmt_reason_setting = select(OptionAttachmentAnomalyReasonSetting).where(
                                and_(
                                    OptionAttachmentAnomalyReasonSetting.checklist_option_uid == att.option_uid,
                                    OptionAttachmentAnomalyReasonSetting.value == reason_val_int
                                )
                            )
                            reason_setting = session.scalar(stmt_reason_setting)
                            if reason_setting:
                                reasons_list.append(reason_setting.name)
                            else:
                                reasons_list.append(reason_val_str)
                        except ValueError:
                            reasons_list.append(reason_val_str)

            if att.anomaly_positions:
                for pos in att.anomaly_positions:
                    pos_parts = []
                    if pos.inv is not None:
                        pos_parts.append(f"inv:{pos.inv}")
                    if pos.mppt is not None:
                        pos_parts.append(f"mppt:{pos.mppt}")
                    if pos.string is not None:
                        pos_parts.append(f"string:{pos.string}")
                    if pos.panel is not None:
                        pos_parts.append(f"panel:{pos.panel}")
                    if pos_parts:
                        positions_list.append(", ".join(pos_parts))

            if att.notes:
                for note_item in att.notes:
                    if note_item.value and note_item.value.strip():
                        notes_list.append(note_item.value.strip())

            reason = " / ".join(reasons_list).strip()
            note_str = " / ".join(notes_list).strip()

            # 若「原因」欄位沒有資料，則自動填寫「說明」內的文字描述
            if not reason and note_str:
                reason = note_str

            position = "; ".join(positions_list)

            opt_sort = option_sort if option_sort is not None else 1
            target_url = f"/checklist/{site_uid}/{check_type}/{checklist_uid}/{table_uid}/#option{opt_sort}"

            output.append({
                "attachment_uid": att.uid,
                "checklist_uid": checklist_uid,
                "option_uid": att.option_uid,
                "site_uid": site_uid,
                "check_type": check_type,
                "table_uid": table_uid,
                "option_sort": opt_sort,
                "site_name": site_name,
                "option_name": option_name,
                "reason": reason,
                "note": note_str,
                "position": position,
                "target_url": target_url
            })

    return jsonify(output)



