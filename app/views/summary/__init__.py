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
        "other": [102, 103, 104],
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

            stmt_count = select(func.count(ChecklistTableOptionData.uid))\
                .join(Checklist, ChecklistTableOptionData.checklist_uid == Checklist.uid)\
                .where(
                    and_(
                        ChecklistTableOptionData.option_uid.in_(uids),
                        ChecklistTableOptionData.value == '異常',
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
        "other": [102, 103, 104],
        "building": [1, 2, 3]
    }

    uids = categories.get(category, [])
    if not uids:
        return jsonify([])

    with session_scope() as session:
        # 1. 查詢符合條件的 ChecklistTableOptionData 以及相關關聯表
        stmt = select(
            ChecklistTableOptionData.checklist_uid,
            ChecklistTableOptionData.option_uid,
            Site.name.label('site_name'),
            ChecklistTableOption.name.label('option_name')
        ).join(
            Checklist, ChecklistTableOptionData.checklist_uid == Checklist.uid
        ).join(
            Site, Checklist.site_uid == Site.uid
        ).join(
            ChecklistTableOption, ChecklistTableOptionData.option_uid == ChecklistTableOption.uid
        ).where(
            and_(
                ChecklistTableOptionData.option_uid.in_(uids),
                ChecklistTableOptionData.value == '異常',
                Checklist.check_date.between(start_date, end_date)
            )
        ).order_by(Checklist.check_date.desc())

        rows = session.execute(stmt).all()

        output = []
        for r in rows:
            # 2. 針對每筆異常資料，查詢對應的 OptionAttachment 記錄
            stmt_attachment = select(OptionAttachment).options(
                selectinload(OptionAttachment.anomaly_reasons),
                selectinload(OptionAttachment.anomaly_positions)
            ).join(
                OptionAttachmentForChecklist, OptionAttachmentForChecklist.option_attachment_uid == OptionAttachment.uid
            ).where(
                and_(
                    OptionAttachment.option_uid == r.option_uid,
                    OptionAttachmentForChecklist.checklist_uid == r.checklist_uid,
                    OptionAttachment.table_type == 'checklist'
                )
            )
            attachments = session.scalars(stmt_attachment).all()

            reason = ""
            position = ""
            
            for att in attachments:
                if att.anomaly_reasons:
                    reason_val_str = att.anomaly_reasons[0].value
                    if reason_val_str:
                        try:
                            reason_val_int = int(reason_val_str)
                            stmt_reason_setting = select(OptionAttachmentAnomalyReasonSetting).where(
                                and_(
                                    OptionAttachmentAnomalyReasonSetting.checklist_option_uid == r.option_uid,
                                    OptionAttachmentAnomalyReasonSetting.value == reason_val_int
                                )
                            )
                            reason_setting = session.scalar(stmt_reason_setting)
                            if reason_setting:
                                reason = reason_setting.name
                            else:
                                reason = reason_val_str
                        except ValueError:
                            reason = reason_val_str
                if att.anomaly_positions:
                    pos = att.anomaly_positions[0]
                    pos_parts = []
                    if pos.inv is not None:
                        pos_parts.append(f"逆變器:{pos.inv}")
                    if pos.mppt is not None:
                        pos_parts.append(f"MPPT:{pos.mppt}")
                    if pos.string is not None:
                        pos_parts.append(f"串:{pos.string}")
                    if pos.panel is not None:
                        pos_parts.append(f"模組:{pos.panel}")
                    if pos_parts:
                        position = ", ".join(pos_parts)

            output.append({
                "checklist_uid": r.checklist_uid,
                "option_uid": r.option_uid,
                "site_name": r.site_name,
                "option_name": r.option_name,
                "reason": reason,
                "position": position
            })

    return jsonify(output)
