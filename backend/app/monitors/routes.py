from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User
from app.monitors.schemas import MonitorCreate, MonitorResponse, ChangeResponse, CheckResult
from app.monitors import service

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get("", response_model=list[MonitorResponse])
def list_monitors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monitors = service.list_monitors(db, user)
    results = []
    for m in monitors:
        r = MonitorResponse.model_validate(m)
        r.change_count = len(m.changes)
        results.append(r)
    return results


@router.post("", response_model=MonitorResponse)
def create_monitor(payload: MonitorCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monitor = service.create_monitor(db, user, payload)
    return MonitorResponse.model_validate(monitor)


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monitor = service.get_monitor(db, user, monitor_id)
    r = MonitorResponse.model_validate(monitor)
    r.change_count = len(monitor.changes)
    return r


@router.delete("/{monitor_id}", status_code=204)
def delete_monitor(monitor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.delete_monitor(db, user, monitor_id)


@router.post("/{monitor_id}/check", response_model=CheckResult)
def check_now(monitor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monitor = service.get_monitor(db, user, monitor_id)
    result = service.run_check(db, monitor)
    return CheckResult(**result)


@router.get("/{monitor_id}/changes", response_model=list[ChangeResponse])
def get_changes(monitor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_changes(db, user, monitor_id)
