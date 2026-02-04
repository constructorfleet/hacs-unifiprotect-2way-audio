"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations

from itertools import groupby

import logging

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from .camera import UniFiProtectProxyCamera
    from .media_player import UniFiProtect2WayAudioPlayer
    from .select import UniFiProtectStreamResolutionSelect, UniFiProtectStreamSecuritySelect


_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


class Unifi2WayAudioDevice:
    """Class for holding groups of entities."""

    def __init__(
        self,
        camera: UniFiProtectProxyCamera,
        media_player: UniFiProtect2WayAudioPlayer,
        security_select: UniFiProtectStreamSecuritySelect | None,
        resolution_select: UniFiProtectStreamResolutionSelect | None,
    ) -> None:
        """Initialize the 2-way audio device."""
        self.camera = camera
        self.media_player = media_player
        self.security_select = security_select
        self.resolution_select = resolution_select


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._devices: dict[str, Unifi2WayAudioDevice] = {}
        self._hass = hass

    def build_entities(self, hass: HomeAssistant) -> None:
        """Build entities from unifiprotect integration."""
        from .camera import UniFiProtectProxyCamera
        from .media_player import UniFiProtect2WayAudioPlayer
        from .select import UniFiProtectStreamResolutionSelect, UniFiProtectStreamSecuritySelect
        
        entity_registry = er.async_get(hass)
        device_registry = dr.async_get(hass)
        unifi_cameras = [
            entity
            for entity
            in entity_registry.entities.values()
            if entity.platform == "unifiprotect" \
                and entity.domain == "camera" \
                and not entity.disabled \
                and not entity.hidden
        ]

        # Group cameras by device_id
        cameras_by_device = {}
        for camera in unifi_cameras:
            if camera.device_id not in cameras_by_device:
                cameras_by_device[camera.device_id] = []
            cameras_by_device[camera.device_id].append(camera)

        for device_id, cameras in cameras_by_device.items():
            unifi_device = device_registry.async_get(device_id)
            if not unifi_device:
                _LOGGER.warning("Device %s not found in registry", device_id)
                continue
                
            # Use the existing UniFi device identifiers so entities group together
            device_info = DeviceInfo(
                identifiers=unifi_device.identifiers,
            )
            
            # Create camera entity
            camera = UniFiProtectProxyCamera(
                self._hass,
                cameras[0].entity_id,
                cameras[0].unique_id,
                unifi_device.name or "Camera",
                device_info,
                self
            )
            
            # Create media player entity
            media_player = UniFiProtect2WayAudioPlayer(
                self._hass, 
                cameras[0].entity_id,
                cameras[0].unique_id,
                device_info,
            )
            
            # Get available options from UniFi Protect camera
            security_options = self._get_available_security_options(hass, cameras[0])
            resolution_options = self._get_available_resolution_options(hass, cameras[0])
            
            # Create security select if there are multiple options
            security_select = None
            if len(security_options) > 1:
                security_select = UniFiProtectStreamSecuritySelect(
                    hass,
                    cameras[0].entity_id,
                    cameras[0].unique_id,
                    unifi_device.name or "Camera",
                    device_info,
                    self,
                    security_options,
                )
                _LOGGER.debug(
                    "Created security select for camera: %s with options: %s",
                    cameras[0].entity_id,
                    security_options,
                )
            
            # Create resolution select if there are multiple options
            resolution_select = None
            if len(resolution_options) > 1:
                resolution_select = UniFiProtectStreamResolutionSelect(
                    hass,
                    cameras[0].entity_id,
                    cameras[0].unique_id,
                    unifi_device.name or "Camera",
                    device_info,
                    self,
                    resolution_options,
                )
                _LOGGER.debug(
                    "Created resolution select for camera: %s with options: %s",
                    cameras[0].entity_id,
                    resolution_options,
                )
            
            # Store the device
            self._devices[cameras[0].unique_id] = Unifi2WayAudioDevice(
                camera,
                media_player,
                security_select,
                resolution_select
            )

    def get_devices(self) -> list[Unifi2WayAudioDevice]:
        """Get all devices."""
        return list(self._devices.values())

    def _get_available_security_options(self, hass: HomeAssistant, camera_entity) -> list[str]:
        """Get available security options for a camera from UniFi Protect.
        
        For now, we return both secure and insecure as most cameras support both.
        In the future, this could query the actual camera capabilities.
        """
        # Try to get the camera object from UniFi Protect integration
        try:
            # Get the UniFi Protect data coordinator
            unifi_entry_id = None
            for entry_id, entry_data in hass.data.get("unifiprotect", {}).items():
                if hasattr(entry_data, "api"):
                    unifi_entry_id = entry_id
                    break
            
            if unifi_entry_id:
                coordinator = hass.data["unifiprotect"][unifi_entry_id]
                # Look up camera by mac address from connections or other identifier
                # For now, return both options as most cameras support both
                return ["Secure", "Insecure"]
        except Exception as err:
            _LOGGER.debug("Could not get security options from UniFi Protect: %s", err)
        
        # Default to both options
        return ["Secure", "Insecure"]

    def _get_available_resolution_options(self, hass: HomeAssistant, camera_entity) -> list[str]:
        """Get available resolution options for a camera from UniFi Protect.
        
        Queries the camera's channels from UniFi Protect to get actual available resolutions.
        """
        # Try to get the camera object from UniFi Protect integration
        try:
            # Get the UniFi Protect data coordinator
            unifi_entry_id = None
            for entry_id, entry_data in hass.data.get("unifiprotect", {}).items():
                if hasattr(entry_data, "api"):
                    unifi_entry_id = entry_id
                    break
            
            if unifi_entry_id:
                coordinator = hass.data["unifiprotect"][unifi_entry_id]
                
                # Try to get camera from coordinator
                if hasattr(coordinator, "data") and hasattr(coordinator.data, "cameras"):
                    # Find the camera by matching the entity_id or unique_id
                    for camera_id, camera_obj in coordinator.data.cameras.items():
                        # Check if this is our camera
                        # The unique_id typically contains the mac address
                        if camera_entity.unique_id and camera_obj.mac and camera_obj.mac in camera_entity.unique_id:
                            # Get channel names from the camera
                            if hasattr(camera_obj, "channels") and camera_obj.channels:
                                channel_names = []
                                for channel in camera_obj.channels:
                                    if hasattr(channel, "name") and channel.name:
                                        # Channel names are typically like "High", "Medium", "Low"
                                        channel_names.append(channel.name)
                                
                                if channel_names:
                                    _LOGGER.debug(
                                        "Found %d channels for camera %s: %s",
                                        len(channel_names),
                                        camera_entity.entity_id,
                                        channel_names
                                    )
                                    return channel_names
        except Exception as err:
            _LOGGER.debug("Could not get resolution options from UniFi Protect: %s", err)
        
        # Default to standard options
        return ["High", "Medium", "Low"]

    def update_stream_security(self, unique_id: str, security: str) -> None:
        """Update stream security for a camera."""
        device = self._devices.get(unique_id)
        if device and device.camera:
            device.camera.update_stream_settings(security=security)
            _LOGGER.debug(
                "Updated security to %s for camera %s", security, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )

    def update_stream_resolution(self, unique_id: str, resolution: str) -> None:
        """Update stream resolution for a camera."""
        device = self._devices.get(unique_id)
        if device and device.camera:
            device.camera.update_stream_settings(resolution=resolution)
            _LOGGER.debug(
                "Updated resolution to %s for camera %s", resolution, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )
