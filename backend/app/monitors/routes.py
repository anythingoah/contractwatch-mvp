from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.auth.dependencies import get_current_user
from app.models import User
from app.monitors.schemas import MonitorCreate, MonitorResponse, ChangeResponse, RecentChangeResponse, CheckResult
from app.monitors import service

router = APIRouter(prefix="/monitors", tags=["monitors"])


def _clamp_pagination(limit: int | None, offset: int) -> tuple[int | None, int]:
    offset = max(offset, 0)
    if limit is None:
        return None, offset
    return min(max(limit, 1), settings.max_page_limit), offset


@router.get("", response_model=list[MonitorResponse])
def list_monitors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = service.list_monitors(db, user)
    results = []
    for monitor, change_count in rows:
        r = MonitorResponse.model_validate(monitor)
        r.change_count = change_count
        results.append(r)
    return results


@router.post("", response_model=MonitorResponse)
def create_monitor(payload: MonitorCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monitor = service.create_monitor(db, user, payload)
    return MonitorResponse.model_validate(monitor)


@router.get("/changes", response_model=list[RecentChangeResponse])
def get_recent_changes(
    limit: int = Query(default=20, ge=1, le=settings.max_page_limit),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cross-monitor activity feed — powers the dashboard's 'recent activity' view."""
    rows = service.list_recent_changes(db, user, limit=limit)
    return [
        RecentChangeResponse(
            id=change.id,
            monitor_id=monitor_id,
            monitor_name=monitor_name,
            change_type=change.change_type,
            severity=change.severity.value,
            summary=change.summary,
            created_at=change.created_at,
        )
        for change, monitor_id, monitor_name in rows
    ]


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
def get_changes(
    monitor_id: int,
    limit: int | None = Query(default=None, ge=1, le=settings.max_page_limit),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    effective_limit, effective_offset = _clamp_pagination(limit, offset)
    return service.list_changes(db, user, monitor_id, limit=effective_limit, offset=effective_offset)