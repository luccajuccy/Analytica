# -*- coding: utf-8 -*-
"""Deterministic ping simulation for fictitious BMS devices."""

import hashlib
from datetime import datetime


def _score(ip, salt="ping"):
    bucket = datetime.now().strftime("%Y%m%d%H%M")
    digest = hashlib.sha256(f"{ip}:{bucket}:{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def ping_device(ip, online_probability=0.85):
    """Return a stable online/offline status plus simulated latency."""
    online = _score(ip) < online_probability
    latency = None if not online else int(4 + _score(ip, "latency") * 180)
    return {
        "ip": ip,
        "status": "online" if online else "offline",
        "online": online,
        "latency_ms": latency,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def ping_ip(ip):
    return ping_device(ip)["online"]


def check_port(ip, port=80):
    return _score(ip, f"port:{port}") < 0.88
