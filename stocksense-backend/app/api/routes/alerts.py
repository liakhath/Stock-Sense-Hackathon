from fastapi import APIRouter, HTTPException

from app.api.deps import Alerts, Engine
from app.schemas.reports import AlertOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(eng: Engine, alerts: Alerts, unread_only: bool = False,
                include_resolved: bool = False):
    """Newest first. Poll this (e.g. every 30s) for the notification bell."""
    alerts.refresh(eng)
    return alerts.list_alerts(unread_only, include_resolved)


@router.get("/count")
def unread_count(eng: Engine, alerts: Alerts):
    alerts.refresh(eng)
    return {"unread": len(alerts.list_alerts(unread_only=True))}


@router.post("/read-all")
def read_all(alerts: Alerts):
    return {"marked": alerts.mark_all_read()}


@router.post("/{alert_id}/read", response_model=AlertOut)
def read_one(alert_id: int, alerts: Alerts):
    a = alerts.mark_read(alert_id)
    if a is None:
        raise HTTPException(404, "Alert not found")
    return a