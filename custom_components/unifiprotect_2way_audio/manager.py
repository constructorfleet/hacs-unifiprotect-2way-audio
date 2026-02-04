"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .camera import UniFiProtectProxyCamera

_LOGGER = logging.getLogger(__name__)


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self) -> None:
        """Initialize the manager."""
        self._cameras: dict[str, UniFiProtectProxyCamera] = {}

    def register_camera(
        self, unique_id: str, camera: UniFiProtectProxyCamera
    ) -> None:
        """Register a camera with the manager."""
        self._cameras[unique_id] = camera
        _LOGGER.debug("Registered camera with unique_id: %s", unique_id)

    def unregister_camera(self, unique_id: str) -> None:
        """Unregister a camera from the manager."""
        if unique_id in self._cameras:
            del self._cameras[unique_id]
            _LOGGER.debug("Unregistered camera with unique_id: %s", unique_id)

    def update_stream_security(self, unique_id: str, security: str) -> None:
        """Update stream security for a camera."""
        camera = self._cameras.get(unique_id)
        if camera:
            camera.update_stream_settings(security=security)
            _LOGGER.debug(
                "Updated security to %s for camera %s", security, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )

    def update_stream_resolution(self, unique_id: str, resolution: str) -> None:
        """Update stream resolution for a camera."""
        camera = self._cameras.get(unique_id)
        if camera:
            camera.update_stream_settings(resolution=resolution)
            _LOGGER.debug(
                "Updated resolution to %s for camera %s", resolution, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )

    def get_available_security_options(self, unique_id: str) -> list[str]:
        """Get available security options for a camera.

        For now, returns all options. In the future, this should query
        the UniFi Protect API to determine actual available options.
        """
        # TODO: Query UniFi Protect API for actual available options
        return ["Secure", "Insecure"]

    def get_available_resolution_options(self, unique_id: str) -> list[str]:
        """Get available resolution options for a camera.

        For now, returns all options. In the future, this should query
        the UniFi Protect API to determine actual available options.
        """
        # TODO: Query UniFi Protect API for actual available options
        return ["High", "Medium", "Low"]
