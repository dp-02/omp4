from flask import Blueprint, render_template, abort, request, session, redirect, url_for
from app.database import session_scope
from sqlalchemy import select
from collections import defaultdict
from app.models import (
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

REGION_MAP = {
    1: "北部",
    2: "中彰投",
    3: "雲嘉南",
    4: "高屏",
    5: "東部",
}


@blueprint.route('/choose_region/')
def choose_region():
    ''' 訪客：選擇地區（免登入） '''
    return render_template('guest/chooseRegion.html')


@blueprint.route('/region/<int:region_index>/')
def region(region_index):
    ''' 訪客：地區案場列表（唯讀） '''
    if region_index not in REGION_MAP:
        return abort(404)
    return render_template(
        'guest/region.html',
        region_name=REGION_MAP[region_index],
        region_index=region_index,
    )

def _guest_has_access(site_uid: int) -> bool:
    access_list = session.get('guest_site_access', [])
    try:
        return int(site_uid) in set(int(x) for x in access_list)
    except Exception:
        return False


def _guest_grant_access(site_uid: int) -> None:
    access_list = session.get('guest_site_access', [])
    try:
        access_set = set(int(x) for x in access_list)
    except Exception:
        access_set = set()
    access_set.add(int(site_uid))
    session['guest_site_access'] = sorted(access_set)


@blueprint.route('/site/<int:site_uid>/unlock/', methods=['POST'])
def unlock_site(site_uid):
    ''' 訪客：輸入案場訪客密碼後解鎖檢視 '''
    guest_password = (request.form.get('guest_password') or '').strip()
    with session_scope() as db_session:
        site_obj = Site.get(db_session, uid=site_uid)
        if not site_obj:
            return abort(404)
        expected = (site_obj.guest_password or '').strip()
        region_index = site_obj.region

    if expected and guest_password == expected:
        _guest_grant_access(site_uid)
        return redirect(url_for('view_guest.site', site_uid=site_uid))

    return redirect(url_for('view_guest.region', region_index=region_index, error='bad_password', site_uid=site_uid))


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
    with session_scope() as session:
        query1 = Site.get(session, uid=site_uid)
        if not query1:
            return abort(404)
        if not _guest_has_access(site_uid):
            return redirect(url_for('view_guest.region', region_index=query1.region, error='need_password', site_uid=site_uid))
        inverter = []
        module = []
        stmt = select(SitePhase).where(SitePhase.site_uid == site_uid)
        query2 = session.scalars(stmt).all()
        for sp_data in query2:
            stmt = select(SitePhaseInverter).where(SitePhaseInverter.phase_uid == sp_data.uid)
            query3 = session.scalars(stmt).all()
            for spi_data in query3:
                inverter.append(SitePhaseInverter.to_dict(spi_data))
            stmt = select(SitePhaseModule).where(SitePhaseModule.phase_uid == sp_data.uid)
            query4 = session.scalars(stmt).all()
            for spm_data in query4:
                module.append(SitePhaseModule.to_dict(spm_data))
        site_dict = Site.to_dict(query1)
        reports_by_year = _reports_by_year(session, site_uid)
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
    if not _guest_has_access(site_uid):
        return redirect(url_for('view_guest.site', site_uid=site_uid))
    with session_scope() as session:
        checklist_obj = Checklist.get(session, uid=checklist_uid)
        if not checklist_obj or checklist_obj.site_uid != site_uid:
            return abort(404)
        check_type = checklist_obj.check_type
        data = _build_full_report_data(session, site_uid, checklist_uid, check_type)
    return render_template('checklist/createReport.html', data=data)
