from flask import Blueprint, render_template, abort, request, session, redirect, url_for
from app.database import session_scope
from sqlalchemy import select
from collections import defaultdict
from app.models import (
    Guest,
    Site,
    SitePhase,
    SitePhaseInverter,
    SitePhaseModule,
    Checklist,
    User,
    ChecklistTable,
    ChecklistTableOption,
    ChecklistTableOptionData,
    OptionAttachment,
    OptionAttachmentForChecklist,
)

blueprint = Blueprint('view_guest', __name__)

import json
from flask import make_response

def _check_guest_access(site_uid):
    if 'user_uid' in session:
        return True
    if 'guest_site_uid' in session and session['guest_site_uid'] == site_uid:
        return True
    return False

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('guest/login.html')
    else:
        account = request.form.get('account')
        password = request.form.get('password')
        with session_scope() as session_db:
            stmt = select(Guest).where(Guest.account == account, Guest.password == password)
            guest = session_db.scalars(stmt).first()
            if guest:
                if not guest.site_uid:
                    msg = "您的帳號尚未綁定任何案場！"
                    resp = make_response(json.dumps({"message": msg}), 422)
                    resp.headers['Content-Type'] = 'application/json'
                    return resp
                
                session['guest_uid'] = guest.uid
                session['guest_site_uid'] = guest.site_uid
                session['guest_account'] = guest.account
                
                response = make_response()
                response.headers['HX-Redirect'] = url_for('view_guest.site', site_uid=guest.site_uid)
                return response
            else:
                msg = "帳號或密碼錯誤，請重新輸入！"
                resp = make_response(json.dumps({"message": msg}), 422)
                resp.headers['Content-Type'] = 'application/json'
                return resp

@blueprint.route('/logout')
def logout():
    session.pop('guest_uid', None)
    session.pop('guest_site_uid', None)
    session.pop('guest_account', None)
    return redirect(url_for('view_guest.login'))


def _reports_by_year(session, site_uid):
    ''' 依年份分組的電廠檢測/維護報告列表（供訪客唯讀） '''
    stmt = (
        select(Checklist)
        .where(Checklist.site_uid == site_uid)
        .order_by(Checklist.check_date.desc())
    )
    rows = session.scalars(stmt).all()
    by_year = defaultdict(list)
    for c in rows:
        year = c.check_date.year if c.check_date else None
        if year is None:
            continue
        user = User.get(session, uid=c.user_uid) if c.user_uid else None
        by_year[year].append({
            "checklist_uid": c.uid,
            "check_type": c.check_type,
            "check_date": c.check_date.isoformat() if c.check_date else "",
            "type_name": "電廠檢測" if c.check_type == 1 else "電廠維修",
            "user_name": user.name if user else None,
        })
    # 年份由新到舊，同一年內按日期新到舊
    years = sorted(by_year.keys(), reverse=True)
    return [{"year": y, "reports": by_year[y]} for y in years]


@blueprint.route('/site/<int:site_uid>/')
def site(site_uid):
    ''' 訪客：案場詳情（唯讀） '''
    if not _check_guest_access(site_uid):
        return abort(403)
        
    with session_scope() as session_db:
        query1 = Site.get(session_db, uid=site_uid)
        if not query1:
            return abort(404)
        inverter = []
        module = []
        stmt = select(SitePhase).where(SitePhase.site_uid == site_uid)
        query2 = session_db.scalars(stmt).all()
        for sp_data in query2:
            stmt = select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == sp_data.uid)
            query3 = session_db.scalars(stmt).all()
            for spi_data in query3:
                inverter.append(SitePhaseInverter.to_dict(spi_data))
            stmt = select(SitePhaseModule).where(SitePhaseModule.phase_uid == sp_data.uid)
            query4 = session_db.scalars(stmt).all()
            for spm_data in query4:
                module.append(SitePhaseModule.to_dict(spm_data))
        site_dict = Site.to_dict(query1)
        reports_by_year = _reports_by_year(session_db, site_uid)
    data = {
        "site": site_dict,
        "inverter": inverter,
        "module": module,
        "reports_by_year": reports_by_year,
    }
    return render_template('guest/site_index.html', data=data)


def _build_full_report_data(session, site_uid, checklist_uid, check_type):
    ''' 組裝「全部項目」的報告資料，與 createReport 相同結構 '''
    data = {
        "site_uid": site_uid,
        "check_type": check_type,
        "checklist_uid": checklist_uid,
        "table": {},
    }
    inverter = []
    module = []
    query_site = Site.get(session, uid=site_uid)
    if query_site:
        data["site"] = Site.to_dict(query_site)
        for sp_data in session.scalars(select(SitePhase).where(SitePhase.site_uid == site_uid)).all():
            for spi_data in session.scalars(select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == sp_data.uid)).all():
                inverter.append(SitePhaseInverter.to_dict(spi_data))
            for spm_data in session.scalars(select(SitePhaseModule).where(SitePhaseModule.phase_uid == sp_data.uid)).all():
                module.append(SitePhaseModule.to_dict(spm_data))
    else:
        data["site"] = None
    data["inverter"] = inverter
    data["module"] = module

    checklist_obj = Checklist.get(session, uid=checklist_uid)
    data["checklist"] = Checklist.to_dict(checklist_obj) if checklist_obj else None
    if checklist_obj and checklist_obj.user_uid:
        user = User.get(session, uid=checklist_obj.user_uid)
        data["inspector_name"] = user.name if user else None
    else:
        data["inspector_name"] = None

    if check_type == 1:
        # 檢測：此 checklist 有資料的所有 table uid
        stmt = (
            select(ChecklistTable.uid)
            .join(ChecklistTableOption, ChecklistTableOption.table_uid == ChecklistTable.uid)
            .join(ChecklistTableOptionData, ChecklistTableOptionData.option_uid == ChecklistTableOption.uid)
            .where(ChecklistTableOptionData.checklist_uid == checklist_uid)
            .distinct()
        )
        final_report_data = [r[0] for r in session.execute(stmt).all()]
    else:
        # 維修：此 checklist 有資料的所有 option uid
        stmt = (
            select(ChecklistTableOptionData.option_uid)
            .where(ChecklistTableOptionData.checklist_uid == checklist_uid)
        )
        all_options = [r[0] for r in session.execute(stmt).all()]
        if not all_options:
            return data

    # 先查所有項目（不含附件），再補上附件，以產出「全部項目」報告
    if check_type == 1:
        stmt = (
            select(ChecklistTableOptionData, ChecklistTableOption, ChecklistTable)
            .join(ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid)
            .join(ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid)
            .where(
                ChecklistTableOptionData.checklist_uid == checklist_uid,
                ChecklistTable.uid.in_(final_report_data),
            )
            .order_by(ChecklistTable.sort)
        )
        rows = session.execute(stmt).all()
        for r in rows:
            ctod, cto, ct = r[0], r[1], r[2]
            if ct.uid not in data["table"]:
                data["table"][ct.uid] = {"name": ct.name, "options": {}}
            if cto.uid not in data["table"][ct.uid]["options"]:
                data["table"][ct.uid]["options"][cto.uid] = {
                    "name": cto.name,
                    "sort": cto.sort,
                    "value": ctod.value,
                    "attachment": [],
                }
        # 附件
        stmt_att = (
            select(OptionAttachment.uid, OptionAttachment.option_uid)
            .join(OptionAttachmentForChecklist, OptionAttachmentForChecklist.option_attachment_uid == OptionAttachment.uid)
            .where(OptionAttachmentForChecklist.checklist_uid == checklist_uid)
        )
        for att_uid, opt_uid in session.execute(stmt_att).all():
            for tid, tdata in data["table"].items():
                if opt_uid in tdata["options"]:
                    tdata["options"][opt_uid]["attachment"].append(att_uid)
                    break
    else:
        stmt = (
            select(ChecklistTableOptionData, ChecklistTableOption, ChecklistTable)
            .join(ChecklistTableOption, ChecklistTableOption.uid == ChecklistTableOptionData.option_uid)
            .join(ChecklistTable, ChecklistTable.uid == ChecklistTableOption.table_uid)
            .where(
                ChecklistTableOptionData.checklist_uid == checklist_uid,
                ChecklistTableOption.uid.in_(all_options),
            )
            .order_by(ChecklistTableOption.sort)
        )
        rows = session.execute(stmt).all()
        for r in rows:
            ctod, cto, ct = r[0], r[1], r[2]
            if ct.uid not in data["table"]:
                data["table"][ct.uid] = {"name": ct.name, "options": {}}
            if cto.uid not in data["table"][ct.uid]["options"]:
                data["table"][ct.uid]["options"][cto.uid] = {
                    "name": cto.name,
                    "sort": cto.sort,
                    "value": ctod.value,
                    "attachment": [],
                }
        stmt_att = (
            select(OptionAttachment.uid, OptionAttachment.option_uid)
            .join(OptionAttachmentForChecklist, OptionAttachmentForChecklist.option_attachment_uid == OptionAttachment.uid)
            .where(OptionAttachmentForChecklist.checklist_uid == checklist_uid)
        )
        for att_uid, opt_uid in session.execute(stmt_att).all():
            for tid, tdata in data["table"].items():
                if opt_uid in tdata["options"]:
                    tdata["options"][opt_uid]["attachment"].append(att_uid)
                    break
    return data


@blueprint.route('/site/<int:site_uid>/report/<int:checklist_uid>/')
def report(site_uid, checklist_uid):
    ''' 訪客：電廠檢測/維護報告（預設產出所有項目，唯讀） '''
    if not _check_guest_access(site_uid):
        return abort(403)
        
    with session_scope() as session_db:
        checklist_obj = Checklist.get(session_db, uid=checklist_uid)
        if not checklist_obj or checklist_obj.site_uid != site_uid:
            return abort(404)
        check_type = checklist_obj.check_type
        data = _build_full_report_data(session_db, site_uid, checklist_uid, check_type)
    return render_template('checklist/createReport.html', data=data)
