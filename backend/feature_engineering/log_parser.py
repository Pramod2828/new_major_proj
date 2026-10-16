import re
import math
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# RFC 3164 pattern: <PRI>Mmm dd hh:mm:ss hostname app[pid]: message
RFC_3164_PATTERN = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>[\w\.\-]+)\s+(?P<service>[\w\.\-\(\)]+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$'
)

# RFC 5424 pattern: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD] MSG
RFC_5424_PATTERN = re.compile(
    r'^<(?P<pri>\d{1,3})>1\s+(?P<timestamp>[^\s]+)\s+(?P<hostname>[^\s]+)\s+'
    r'(?P<service>[^\s]+)\s+(?P<pid>[^\s]+)\s+(?P<msgid>[^\s]+)\s*'
    r'(?:\[(?P<sd>[^\]]*)\])?\s*(?P<message>.*)$'
)

# ISO timestamp standard pattern: YYYY-MM-DD HH:MM:SS [LEVEL] [service]: message
ISO_LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+'
    r'(?:\[?(?P<level>[A-Z]+)\]?\s+)?(?:(?P<hostname>[\w\.\-]+)\s+)?'
    r'(?:(?P<service>[\w\.\-\/]+?)(?:\[(?P<pid>\d+)\])?:?\s+)?(?P<message>.*)$'
)

# Extraction regexes
IP_REGEX = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
USER_REGEX = re.compile(r'(?:user(?:name)?|for|by)\s*[=:]?\s*["\']?([a-zA-Z0-9_\-\.]{2,32})["\']?', re.IGNORECASE)

SEVERITY_MAP = {
    "emerg": 0, "emergency": 0, "panic": 0,
    "alert": 1,
    "crit": 2, "critical": 2,
    "err": 3, "error": 3,
    "warn": 4, "warning": 4,
    "notice": 5,
    "info": 6, "information": 6,
    "debug": 7, "trace": 7
}

class LogParser:
    """Modular parser for standard syslogs, structured JSON logs, and arbitrary text records."""

    @classmethod
    def parse_line(cls, line: str) -> Dict[str, Any]:
        """Parse a single raw log string into structured dictionary."""
        line = line.strip()
        if not line:
            return cls._empty_record("")

        # 1. Attempt JSON parsing
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                return cls._normalize_json_record(data, line)
            except Exception:
                pass

        # 2. Attempt RFC 5424
        match = RFC_5424_PATTERN.match(line)
        if match:
            gd = match.groupdict()
            pri = int(gd["pri"]) if gd.get("pri") else None
            sev, fac = cls._decode_pri(pri)
            return cls._clean_record({
                "raw": line,
                "timestamp": gd.get("timestamp"),
                "hostname": gd.get("hostname"),
                "service": gd.get("service"),
                "pid": gd.get("pid"),
                "severity": sev,
                "facility": fac,
                "message": gd.get("message", "")
            })

        # 3. Attempt RFC 3164
        match = RFC_3164_PATTERN.match(line)
        if match:
            gd = match.groupdict()
            pri = int(gd["pri"]) if gd.get("pri") else None
            sev, fac = cls._decode_pri(pri)
            return cls._clean_record({
                "raw": line,
                "timestamp": gd.get("timestamp"),
                "hostname": gd.get("hostname"),
                "service": gd.get("service"),
                "pid": gd.get("pid"),
                "severity": sev,
                "facility": fac,
                "message": gd.get("message", "")
            })

        # 4. Attempt ISO standard pattern
        match = ISO_LOG_PATTERN.match(line)
        if match:
            gd = match.groupdict()
            lvl = gd.get("level")
            sev = SEVERITY_MAP.get(lvl.lower()) if lvl else 6
            return cls._clean_record({
                "raw": line,
                "timestamp": gd.get("timestamp"),
                "hostname": gd.get("hostname") or "localhost",
                "service": gd.get("service") or "system",
                "pid": gd.get("pid"),
                "severity": sev,
                "facility": 1,
                "message": gd.get("message", line)
            })

        # 5. Fallback unstructured line
        return cls._clean_record({
            "raw": line,
            "timestamp": None,
            "hostname": "localhost",
            "service": "unknown",
            "pid": None,
            "severity": 6,
            "facility": 1,
            "message": line
        })

    @classmethod
    def parse_batch(cls, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse multiple log lines into structured dictionaries."""
        return [cls.parse_line(line) for line in lines if line.strip()]

    @classmethod
    def extract_features(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract candidate numerical and categorical features from a parsed log record."""
        msg = str(record.get("message") or "")
        msg_lower = msg.lower()

        # Keyword checks
        has_error = int(any(k in msg_lower for k in ["error", "fail", "failed", "failure", "fatal", "exception", "crash"]))
        has_warning = int(any(k in msg_lower for k in ["warn", "warning", "caution", "alert"]))
        has_auth = int(any(k in msg_lower for k in ["auth", "login", "session", "password", "sshd", "sudo", "pam"]))
        has_failed_auth = int(any(k in msg_lower for k in ["failed password", "authentication failure", "invalid user", "failed login"]))
        has_denied = int(any(k in msg_lower for k in ["denied", "forbidden", "unauthorized", "rejected", "blocked"]))

        # IP address extraction
        ip_match = IP_REGEX.search(msg)
        has_ip = 1 if ip_match else 0
        src_ip = ip_match.group(0) if ip_match else None

        # User extraction
        user_match = USER_REGEX.search(msg)
        username = user_match.group(1) if user_match else None

        # Message metrics
        msg_len = len(msg)
        tokens = msg.split()
        token_count = len(tokens)
        digits_count = sum(c.isdigit() for c in msg)
        digit_ratio = round(digits_count / msg_len, 4) if msg_len > 0 else 0.0
        entropy = cls._calculate_entropy(msg)

        # Note: severity is intentionally excluded from the returned feature dict.
        # In AIT-LDS datasets (and the live Windows collector fallback), severity
        # defaults to 6 (INFO) for virtually all records — std=0, zero discriminative
        # power. The raw severity value is still stored in the parsed record dict
        # (accessible via record["severity"]) for diagnostic use; it is simply not
        # emitted as a training feature to avoid polluting the feature matrix.

        return {
            "message_length": msg_len,
            "token_count": token_count,
            "digit_ratio": digit_ratio,
            "entropy": entropy,
            "has_error": has_error,
            "has_warning": has_warning,
            "has_auth": has_auth,
            "has_failed_auth": has_failed_auth,
            "has_denied": has_denied,
            "has_ip": has_ip,
            "service": str(record.get("service") or "unknown"),
            "hostname": str(record.get("hostname") or "localhost"),
            "source_ip": src_ip,
            "username": username,
            "severity_level": record.get("severity")
        }

    @staticmethod
    def _calculate_entropy(text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum(p * math.log2(p) for p in prob)
        return round(entropy, 4)

    @staticmethod
    def _decode_pri(pri: Optional[int]):
        """Decode RFC syslog priority into severity and facility."""
        if pri is None:
            return 6, 1
        facility = pri // 8
        severity = pri % 8
        return severity, facility

    @classmethod
    def _normalize_json_record(cls, data: dict, raw: str) -> Dict[str, Any]:
        """Normalize JSON log keys into standard record."""
        # Check potential timestamp fields
        ts = data.get("timestamp") or data.get("time") or data.get("@timestamp") or data.get("datetime")
        host = data.get("hostname") or data.get("host") or data.get("server") or "localhost"
        service = data.get("service") or data.get("app") or data.get("program") or data.get("logger") or "unknown"
        pid = data.get("pid") or data.get("process_id")
        msg = data.get("message") or data.get("msg") or data.get("log") or raw
        level = data.get("level") or data.get("severity") or "info"
        sev = SEVERITY_MAP.get(str(level).lower(), 6)

        return cls._clean_record({
            "raw": raw,
            "timestamp": str(ts) if ts else None,
            "hostname": str(host),
            "service": str(service),
            "pid": str(pid) if pid else None,
            "severity": sev,
            "facility": 1,
            "message": str(msg)
        })

    @staticmethod
    def _empty_record(raw: str) -> Dict[str, Any]:
        return {
            "raw": raw,
            "timestamp": None,
            "hostname": "localhost",
            "service": "unknown",
            "pid": None,
            "severity": 6,
            "facility": 1,
            "message": ""
        }

    @classmethod
    def _clean_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich record with IP and user if present in message."""
        msg = record.get("message", "")
        ip_match = IP_REGEX.search(msg)
        if ip_match and not record.get("source_ip"):
            record["source_ip"] = ip_match.group(0)
        user_match = USER_REGEX.search(msg)
        if user_match and not record.get("username"):
            record["username"] = user_match.group(1)
        return record
