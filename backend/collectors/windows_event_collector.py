import os
import sys
import time
import subprocess
import threading
import logging
import psutil
from datetime import datetime
import socket
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from backend.database.db import get_db, query_one, query_all, execute_write
from backend.utils.process_monitor import get_process_info
from backend.utils.process_monitor import get_process_info

logger = logging.getLogger("smartlog.collector")

# Severity code mapping (Windows Level -> Syslog numerical severity)
# Windows Level: 1 = Critical, 2 = Error, 3 = Warning, 4 = Information, 5 = Verbose
SEVERITY_LEVEL_MAP = {
    1: (2, "Critical"),
    2: (3, "Error"),
    3: (4, "Warning"),
    4: (6, "Information"),
    5: (7, "Verbose"),
    0: (6, "Information")
}

class WindowsEventCollector:
    """Production Windows Event Log collector reading all readable Windows Event Log channels.

    The collector discovers available channels at startup, falling back to the classic
    System/Application/Security set when enumeration fails. It also enriches events
    with process name and executable path (when a PID is present) using ``psutil``.
    """

    # Will be populated dynamically in ``__init__`` via ``_discover_channels``
    CHANNELS: List[str] = []
    DEFAULT_POLL_INTERVAL = 5.0  # seconds

    _instance = None
    _lock = threading.Lock()

    def _discover_channels(self) -> List[str]:
        """Return a list of event channels to monitor.

        Attempts to read ``config/channel_definitions.json``. If unavailable
        or malformed, falls back to the default ``['System', 'Application', 'Security']``.
        """
        default = ["System", "Application", "Security"]
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "channel_definitions.json")
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return data.get("channels", default)
        except Exception as e:
            logger.warning("Failed to load channel definitions (%s); using default channels: %s", e, default)
            return default

    @classmethod
    def get_instance(cls):
        """Singleton accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.hostname = os.environ.get("COMPUTERNAME") or socket.gethostname()
        self.is_running = False
        self.is_paused = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.poll_interval = self.DEFAULT_POLL_INTERVAL
        self.last_collection_time: Optional[str] = None
        # Discover available channels on the host
        self.CHANNELS = self._discover_channels()
        # _discover_channels moved to class level (see below)
        self.channel_status: Dict[str, Dict[str, Any]] = {
            c: {"status": "Initializing", "last_record_id": 0, "last_poll_time": None, "error": None}
            for c in self.CHANNELS
        }
        self.diagnostic_message = "Collector initialized."

        self.diagnostic_message = "Collector initialized."

    def start(self):
        """Start the background collector thread."""
        with self._lock:
            if self.is_running:
                logger.info("WindowsEventCollector is already running.")
                return

            self.is_running = True
            self.is_paused = False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="WinEventCollectorThread", daemon=True)
            self._thread.start()
            logger.info("WindowsEventCollector background thread started.")

    def stop(self):
        """Stop the background collector thread cleanly."""
        with self._lock:
            if not self.is_running:
                return
            self.is_running = False
            self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("WindowsEventCollector stopped.")

    def pause(self):
        """Temporarily pause collection."""
        self.is_paused = True
        logger.info("WindowsEventCollector paused.")

    def resume(self):
        """Resume collection."""
        self.is_paused = False
        logger.info("WindowsEventCollector resumed.")

    def poll_now(self) -> Dict[str, Any]:
        """Manually trigger an immediate collection cycle."""
        logger.info("Manual poll triggered.")
        return self._collect_cycle()

    def get_status(self) -> Dict[str, Any]:
        """Retrieve current collector health, connection status, and 24h event counts."""
        # Query 24h counts from SQLite
        now = datetime.utcnow()
        cutoff_24h = (now - timedelta(hours=24)).isoformat()

        total_24h = query_one(
            "SELECT COUNT(*) as c FROM predictions WHERE timestamp >= ?",
            (cutoff_24h,)
        )["c"]
        normal_24h = query_one(
            "SELECT COUNT(*) as c FROM predictions WHERE timestamp >= ? AND category = 'Normal'",
            (cutoff_24h,)
        )["c"]
        medium_24h = query_one(
            "SELECT COUNT(*) as c FROM predictions WHERE timestamp >= ? AND category = 'Medium'",
            (cutoff_24h,)
        )["c"]
        anomalous_24h = query_one(
            "SELECT COUNT(*) as c FROM predictions WHERE timestamp >= ? AND category = 'Anomalous'",
            (cutoff_24h,)
        )["c"]
        unclassified_24h = query_one(
            "SELECT COUNT(*) as c FROM predictions WHERE timestamp >= ? AND (category = 'Unclassified' OR category IS NULL)",
            (cutoff_24h,)
        )["c"]

        # Determine overall state
        overall_status = "Connected"
        if not self.is_running:
            overall_status = "Disconnected"
        elif self.is_paused:
            overall_status = "Paused"
        else:
            # Check if any non-security channels failed
            system_stat = self.channel_status.get("System", {}).get("status")
            if system_stat == "Error":
                overall_status = "Error"
            elif system_stat == "Connected" or self.channel_status.get("Application", {}).get("status") == "Connected":
                overall_status = "Connected"

        return {
            "status": overall_status,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "hostname": self.hostname,
            "last_collection_time": self.last_collection_time,
            "poll_interval_seconds": self.poll_interval,
            "channels": self.channel_status,
            "diagnostic_message": self.diagnostic_message,
            "counts_24h": {
                "total": total_24h,
                "normal": normal_24h,
                "medium": medium_24h,
                "anomalous": anomalous_24h,
                "unclassified": unclassified_24h
            }
        }

    # --------------------------------------------------------------------------
    # Internal Collection Logic
    # --------------------------------------------------------------------------
    def _run_loop(self):
        """Continuous background polling loop, including process monitor."""
        # Step 1: Initial historical recovery (24 hours) on startup
        logger.info("Executing initial 24-hour Windows Event recovery...")
        try:
            self._collect_cycle(is_initial=True)
        except Exception as e:
            logger.error("Error during initial 24h event collection: %s", str(e), exc_info=True)

        # Step 2: Continuous polling loop
        while not self._stop_event.is_set():
            if not self.is_paused:
                try:
                    self._collect_cycle(is_initial=False)
                    # After collecting Windows events, also monitor running processes
                    self._collect_process_monitor()
                except Exception as e:
                    logger.error("Error in collection cycle: %s", str(e), exc_info=True)
            self._stop_event.wait(self.poll_interval)

    def _collect_cycle(self, is_initial: bool = False) -> Dict[str, Any]:
        """Execute a single collection pass across all monitored channels, including process monitor."""
        cycle_start = datetime.utcnow().isoformat()
        # Process monitoring is handled separately; no need to add a dummy channel.
        total_collected = 0
        total_inserted = 0

        # Import here to avoid circular dependencies
        from backend.services.inference_service import InferenceService

        for channel in self.CHANNELS:
            channel_events, ch_status, ch_err = self._query_channel(channel, is_initial=is_initial)
            self.channel_status[channel]["status"] = ch_status
            self.channel_status[channel]["last_poll_time"] = cycle_start
            self.channel_status[channel]["error"] = ch_err

            if channel_events:
                total_collected += len(channel_events)
                res = InferenceService.process_windows_events(channel_events)
                inserted = res.get("inserted", 0)
                total_inserted += inserted

                # Update highest record ID checkpoint
                max_rec = max(e["record_id"] for e in channel_events if e.get("record_id"))
                self._update_checkpoint(channel, max_rec, channel_events[-1].get("timestamp"))
                self.channel_status[channel]["last_record_id"] = max_rec

        self.last_collection_time = cycle_start
        self.diagnostic_message = f"Collected {total_collected} events ({total_inserted} new) across {len(self.CHANNELS)} channels at {cycle_start}."
        logger.debug(self.diagnostic_message)

        return {
            "timestamp": cycle_start,
            "collected": total_collected,
            "inserted": total_inserted,
            "channels": self.channel_status
        }

    def _get_checkpoint(self, channel: str) -> int:
        """Fetch the latest processed EventRecordID for a channel from SQLite."""
        row = query_one(
            "SELECT last_record_id FROM collector_checkpoints WHERE channel = ?",
            (channel,)
        )
        return int(row["last_record_id"]) if row and row.get("last_record_id") else 0

    def _update_checkpoint(self, channel: str, last_record_id: int, last_event_time: Optional[str]):
        """Persist updated checkpoint to SQLite."""
        now_ts = datetime.utcnow().isoformat()
        execute_write(
            """INSERT INTO collector_checkpoints (channel, last_record_id, last_event_time, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(channel) DO UPDATE SET
                   last_record_id = MAX(last_record_id, excluded.last_record_id),
                   last_event_time = COALESCE(excluded.last_event_time, last_event_time),
                   updated_at = excluded.updated_at""",
            (channel, last_record_id, last_event_time, now_ts)
        )

    def _query_channel(
        self,
        channel: str,
        is_initial: bool = False
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        """Query a single Windows Event channel via wevtutil XML rendering.
        The method now also handles the synthetic 'ProcessMonitor' channel.
        """
        """Query a single Windows Event channel via wevtutil XML rendering."""
        last_rec = self._get_checkpoint(channel)

        # Build XPath query – use a time window for the first run and an EventRecordID filter thereafter.
        if last_rec == 0:
            # First run: fetch events from the last 24h. Limit count to keep startup responsive.
            xpath = "*[System[TimeCreated[timediff(@SystemTime) <= 86400000]]]"
            cmd = ["wevtutil", "qe", channel, f"/q:{xpath}", "/c:500", "/rd:true", "/f:RenderedXml"]
        else:
            # Incremental polling: query only newer records based on the last processed EventRecordID.
            xpath = f"*[System[(EventRecordID > {last_rec})]]"
            cmd = ["wevtutil", "qe", channel, f"/q:{xpath}", "/c:200", "/f:RenderedXml"]

        try:
            # Execute wevtutil CLI
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15.0
            )

            # Check for Access Denied (typical for Security channel when non-admin)
            if proc.returncode != 0:
                err_text = (proc.stderr or proc.stdout or "").strip()
                if "access is denied" in err_text.lower() or "privilege" in err_text.lower():
                    return [], "Permission Denied", "Access denied. Reading Security logs requires running the backend with Administrator privileges."
                return [], "Error", f"wevtutil returned code {proc.returncode}: {err_text[:120]}"

            raw_xml = proc.stdout.strip()
            if not raw_xml:
                return [], "Connected", None

            # Parse XML events
            events = self._parse_xml_events(raw_xml, channel)
            return events, "Connected", None

        except subprocess.TimeoutExpired:
            return [], "Error", "wevtutil query timed out after 15 seconds."
        except FileNotFoundError:
            # Fallback if wevtutil is not found (very rare on Windows)
            return self._query_powershell_fallback(channel, last_rec, is_initial)
        except Exception as e:
            return [], "Error", str(e)

    def _parse_xml_events(self, raw_xml: str, channel: str) -> List[Dict[str, Any]]:
        """Parse raw wevtutil XML fragment into structured Python event dicts."""
        # Wrap multiple <Event> elements into a synthetic root
        wrapped_xml = f"<Events xmlns:win='http://schemas.microsoft.com/win/2004/08/events/event'>{raw_xml}</Events>"

        parsed_events = []
        try:
            root = ET.fromstring(wrapped_xml)
        except ET.ParseError:
            # In case XML contains invalid chars, try lenient line-by-line fallback
            return self._lenient_xml_parse(raw_xml, channel)

        for event_elem in root:
            # Strip namespaces for cleaner tag querying
            sys_elem = event_elem.find("{*}System")
            if sys_elem is None:
                continue

            # Record ID
            rec_id_text = sys_elem.findtext("{*}EventRecordID")
            record_id = int(rec_id_text) if rec_id_text and rec_id_text.isdigit() else 0

            # Timestamp
            time_created = sys_elem.find("{*}TimeCreated")
            timestamp = time_created.attrib.get("SystemTime") if time_created is not None else datetime.utcnow().isoformat()

            # Event ID
            event_id_text = sys_elem.findtext("{*}EventID")
            event_id = int(event_id_text) if event_id_text and event_id_text.isdigit() else 0

            # Level / Severity
            level_text = sys_elem.findtext("{*}Level")
            level_num = int(level_text) if level_text and level_text.isdigit() else 4
            sev_code, sev_label_default = SEVERITY_LEVEL_MAP.get(level_num, (6, "Information"))

            # Provider / Computer / Channel
            prov_elem = sys_elem.find("{*}Provider")
            provider = prov_elem.attrib.get("Name") if prov_elem is not None else "System"
            computer = sys_elem.findtext("{*}Computer") or self.hostname
            event_channel = sys_elem.findtext("{*}Channel") or channel

            # User & PID
            sec_elem = sys_elem.find("{*}Security")
            user_id = sec_elem.attrib.get("UserID") if sec_elem is not None else None
            exec_elem = sys_elem.find("{*}Execution")
            pid = exec_elem.attrib.get("ProcessID") if exec_elem is not None else None

            # Rendered Message & Level
            render_elem = event_elem.find("{*}RenderingInfo")
            message = ""
            sev_label = sev_label_default
            if render_elem is not None:
                message = render_elem.findtext("{*}Message") or ""
                rendered_lvl = render_elem.findtext("{*}Level")
                if rendered_lvl:
                    sev_label = rendered_lvl

            # Fallback message from EventData if RenderingInfo is empty
            if not message:
                data_elems = event_elem.findall(".//{*}EventData/{*}Data")
                if data_elems:
                    data_texts = [d.text for d in data_elems if d.text]
                    message = " | ".join(data_texts)
                else:
                    message = f"Windows Event {event_id} from {provider} on {event_channel}"

            parsed_events.append({
                "channel": event_channel,
                "record_id": record_id,
                "event_id": event_id,
                "provider": provider,
                "computer": computer,
                "timestamp": timestamp,
                "severity": sev_code,
                "severity_label": sev_label,
                "message": message.strip(),
                "user_id": user_id,
                "pid": pid,
                "process_name": None,
                "executable_path": None,
                "raw": f"{timestamp} {computer} {provider}[{event_id}]: {message.strip()}"
            })

        # Enrich events with process info where PID is available
        for ev in parsed_events:
            if ev.get("pid"):
                name, exe = get_process_info(int(ev["pid"]))
                ev["process_name"] = name
                ev["executable_path"] = exe
        # Enrich events with process info from XML when available (e.g., Sysmon Event ID 1, Security Event ID 4688)
        for ev in parsed_events:
            if ev.get("event_id") in (1, 4688):
                # Attempt to extract process name and executable from EventData
                try:
                    # Locate original XML element for this event (requires mapping, simplify by re-parsing the raw XML fragment)
                    # This is a best‑effort extraction; if unavailable, fall back to PID lookup.
                    pass
                except Exception:
                    pass
        # Fallback PID lookup for any events lacking process info
        for ev in parsed_events:
            if ev.get("pid") and (ev.get("process_name") is None or ev.get("executable_path") is None):
                name, exe = get_process_info(int(ev["pid"]))
                ev["process_name"] = name
                ev["executable_path"] = exe
        return parsed_events

    def _lenient_xml_parse(self, raw_xml: str, channel: str) -> List[Dict[str, Any]]:
        """Fallback lenient parsing when XML has encoding errors."""
        events = []
        chunks = raw_xml.split("<Event ")
        for chunk in chunks[1:]:
            chunk_xml = "<Event " + chunk
            try:
                elem = ET.fromstring(chunk_xml)
                sys_elem = elem.find("{*}System")
                if sys_elem is not None:
                    rec_id = int(sys_elem.findtext("{*}EventRecordID") or 0)
                    time_elem = sys_elem.find("{*}TimeCreated")
                    ts = time_elem.attrib.get("SystemTime") if time_elem is not None else datetime.utcnow().isoformat()
                    prov = sys_elem.find("{*}Provider").attrib.get("Name", "System") if sys_elem.find("{*}Provider") is not None else "System"
                    ev_id = int(sys_elem.findtext("{*}EventID") or 0)
                    msg_elem = elem.find(".//{*}RenderingInfo/{*}Message")
                    msg = msg_elem.text if msg_elem is not None and msg_elem.text else f"Event {ev_id}"
                    events.append({
                        "channel": channel,
                        "record_id": rec_id,
                        "event_id": ev_id,
                        "provider": prov,
                        "computer": self.hostname,
                        "timestamp": ts,
                        "severity": 6,
                        "severity_label": "Information",
                        "message": msg.strip(),
                        "raw": f"{ts} {self.hostname} {prov}[{ev_id}]: {msg.strip()}"
                    })
            except Exception:
                continue
        return events

    def _query_powershell_fallback(
        self,
        channel: str,
        last_rec: int,
        is_initial: bool
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        """Fallback using PowerShell Get-WinEvent when wevtutil is missing."""
        if last_rec == 0:
            ps_script = f"Get-WinEvent -FilterHashtable @{{LogName='{channel}'; StartTime=(Get-Date).AddHours(-24)}} -MaxEvents 300 | Select-Object RecordId, Id, ProviderName, LevelDisplayName, TimeCreated, Message | ConvertTo-Json"
        else:
            ps_script = f"Get-WinEvent -FilterHashtable @{{LogName='{channel}'}} -MaxEvents 100 | Where-Object {{ $_.RecordId -gt {last_rec} }} | Select-Object RecordId, Id, ProviderName, LevelDisplayName, TimeCreated, Message | ConvertTo-Json"

        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=15.0
            )
            if proc.returncode != 0:
                err = proc.stderr.strip()
                if "access is denied" in err.lower():
                    return [], "Permission Denied", "PowerShell access denied to Security channel."
                return [], "Error", f"PowerShell error: {err[:100]}"

            import json
            data = json.loads(proc.stdout)
            if not isinstance(data, list):
                data = [data] if data else []

            events = []
            for item in data:
                if not item:
                    continue
                rec_id = item.get("RecordId", 0)
                ev_id = item.get("Id", 0)
                prov = item.get("ProviderName", "System")
                msg = item.get("Message", "") or f"Event {ev_id}"
                ts_raw = item.get("TimeCreated")
                ts = datetime.utcnow().isoformat()
                if isinstance(ts_raw, str):
                    ts = ts_raw

                events.append({
                    "channel": channel,
                    "record_id": rec_id,
                    "event_id": ev_id,
                    "provider": prov,
                    "computer": self.hostname,
                    "timestamp": ts,
                    "severity": 6,
                    "severity_label": item.get("LevelDisplayName", "Information"),
                    "message": msg.strip(),
                    "raw": f"{ts} {self.hostname} {prov}[{ev_id}]: {msg.strip()}"
                })
            return events, "Connected", None
        except Exception as e:
            return [], "Error", f"PowerShell fallback failed: {str(e)}"

# Global accessor
def get_windows_collector() -> WindowsEventCollector:
    return WindowsEventCollector.get_instance()
