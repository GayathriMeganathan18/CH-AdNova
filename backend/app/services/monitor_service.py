import logging
from datetime import date, datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from app.analytics.anomaly import detect_anomaly
from app.config import Settings
from app.schemas.investigation import InvestigationRequest

logger = logging.getLogger("ch_adnova.monitor")

MONITORED_METRICS: tuple[str, ...] = (
    "revenue", "requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks"
)

def _dedup_id(metric: str, target_date: date, strategy: str) -> str:
    return f"sched:{metric}:{target_date}:{strategy}"

def _root_cause_summary(investigation_result) -> str:
    if not investigation_result.root_causes:
        return "No concentrated root cause - anomaly appears broad-based."
    top = investigation_result.root_causes[0].hypothesis
    return f'{top.dimension} = "{top.value}"'


def run_cycle(repo, anomaly_store, investigation_service, settings: Settings) -> list[dict]:
    summary: list[dict] = []

    try:
        _, max_date = repo.data_date_range()
    except Exception:
        logger.exception("monitor: failed to read data date range")
        return summary
    if max_date is None:
        return summary 

    for metric in MONITORED_METRICS:
        entry = {"metric": metric, "target_date": str(max_date), "is_anomalous": False, "triggered": False}
        try:
            result = detect_anomaly(
                repo, metric, max_date, settings.monitor_baseline_days, strategy=settings.monitor_strategy
            )
        except Exception:
            logger.exception("monitor: anomaly detection failed for metric=%s", metric)
            summary.append(entry)
            continue

        entry["is_anomalous"] = result.is_anomalous
        entry["severity"] = result.severity
        if not result.is_anomalous:
            summary.append(entry)
            continue

        dedup_id = _dedup_id(metric, max_date, settings.monitor_strategy)
        if anomaly_store.get(dedup_id) is not None:
            entry["already_alerted"] = True
            summary.append(entry)
            continue

        record = result.to_dict()
        record["status"] = "detected"
        record["source"] = "scheduler"
        anomaly_store.save(dedup_id, record)
        entry["alert_id"] = dedup_id

        try:
            inv_result = investigation_service.run_investigation(
                InvestigationRequest(
                    metric=metric, target_date=max_date, baseline_days=settings.monitor_baseline_days
                )
            )
            anomaly_store.attach_investigation(
                dedup_id, inv_result.investigation_id,
                _root_cause_summary(inv_result), inv_result.executive_summary,
            )
            entry["triggered"] = True
            entry["investigation_id"] = inv_result.investigation_id
        except Exception:
            logger.exception("monitor: auto-triggered investigation failed for metric=%s", metric)

        summary.append(entry)

    return summary


class MonitorService:
    def __init__(self, repo, anomaly_store, investigation_service, settings: Settings):
        self._repo = repo
        self._anomaly_store = anomaly_store
        self._investigation_service = investigation_service
        self._settings = settings
        self._scheduler = BackgroundScheduler(daemon=True)
        self.last_run_at: str | None = None
        self.last_results: list[dict] = []

    def _tick(self) -> None:
        self.last_results = run_cycle(
            self._repo, self._anomaly_store, self._investigation_service, self._settings
        )
        self.last_run_at = datetime.now(timezone.utc).isoformat()

    def run_now(self) -> list[dict]:
        self._tick()
        return self.last_results

    def start(self) -> None:
        if not self._settings.monitor_enabled:
            logger.info("monitor: disabled via settings, not starting")
            return
        self._scheduler.add_job(
            self._tick,
            "interval",
            seconds=self._settings.monitor_interval_seconds,
            id="metric_monitor",
            next_run_time=datetime.now(), 
        )
        self._scheduler.start()
        logger.info("monitor: started, interval=%ss, strategy=%s", self._settings.monitor_interval_seconds, self._settings.monitor_strategy)

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def status(self) -> dict:
        return {
            "enabled": self._settings.monitor_enabled,
            "interval_seconds": self._settings.monitor_interval_seconds,
            "strategy": self._settings.monitor_strategy,
            "monitored_metrics": list(MONITORED_METRICS),
            "running": self._scheduler.running,
            "last_run_at": self.last_run_at,
            "last_results": self.last_results,
        }


_monitor_singleton: MonitorService | None = None


def init_monitor_service(repo, anomaly_store, investigation_service, settings: Settings) -> MonitorService:
    global _monitor_singleton
    _monitor_singleton = MonitorService(repo, anomaly_store, investigation_service, settings)
    return _monitor_singleton


def get_monitor_service() -> MonitorService:
    if _monitor_singleton is None:
        raise RuntimeError("Monitor service not initialized - init_monitor_service() must run at app startup")
    return _monitor_singleton
