"""Frontend utilities for UniFi Protect 2-Way Audio."""
import logging
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def register_static_path(hass: HomeAssistant, url_path: str, path: str):
    """Register a static path for serving files."""
    # Home Assistant 2024.7 introduced StaticPathConfig for async path registration
    if (MAJOR_VERSION, MINOR_VERSION) >= (2024, 7):
        from homeassistant.components.http import StaticPathConfig

        # Third parameter (True) enables cache headers for better performance
        await hass.http.async_register_static_paths(
            [StaticPathConfig(url_path, path, True)]
        )
    else:
        # Fallback for older versions - synchronous registration without cache headers
        hass.http.register_static_path(url_path, path)


async def init_resource(hass: HomeAssistant, url: str, ver: str) -> bool:
    """Add extra JS module for lovelace mode YAML and new lovelace resource
    for mode GUI. It's better to add extra JS for all modes, because it has
    random url to avoid problems with the cache. But chromecast don't support
    extra JS urls and can't load custom card.
    """
    try:
        lovelace = hass.data.get("lovelace")
        if not lovelace:
            _LOGGER.warning("Lovelace not available")
            return False

        # Try to get resources from lovelace object
        if hasattr(lovelace, "resources"):
            resources: ResourceStorageCollection = lovelace.resources
        elif isinstance(lovelace, dict):
            resources: ResourceStorageCollection = lovelace.get("resources")
        else:
            _LOGGER.warning("Lovelace resources not accessible")
            return False

        if not resources:
            _LOGGER.warning("Lovelace resources not available")
            return False

        # force load storage
        await resources.async_get_info()

        url2 = f"{url}?v={ver}"

        for item in resources.async_items():
            # Ensure item is a dictionary-like object
            if not isinstance(item, dict):
                continue

            if not item.get("url", "").startswith(url):
                continue

            # no need to update
            if item["url"].endswith(ver):
                _LOGGER.debug("Resource already at version %s", ver)
                return False

            _LOGGER.debug("Update lovelace resource to: %s", url2)

            if isinstance(resources, ResourceStorageCollection):
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url2}
                )
            else:
                # not the best solution, but what else can we do
                item["url"] = url2

            return True

        if isinstance(resources, ResourceStorageCollection):
            _LOGGER.debug("Add new lovelace resource: %s", url2)
            await resources.async_create_item({"res_type": "module", "url": url2})
        else:
            _LOGGER.debug("Add extra JS module: %s", url2)
            add_extra_js_url(hass, url2)

        return True
    except Exception as err:
        _LOGGER.error("Error initializing resource: %s", err, exc_info=True)
        return False
