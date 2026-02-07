"""Switch platform for UniFi Protect 2-Way Audio - imports from microphone module."""
from __future__ import annotations

from .microphone import async_setup_entry, MicrophoneEntity

__all__ = ["async_setup_entry", "MicrophoneEntity"]
