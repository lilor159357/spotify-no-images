import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.getcwd())

import core.sources.aurora as aurora_module


class _Proto:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def HasField(self, name: str) -> bool:
        return hasattr(self, name) and getattr(self, name) is not None


class _Response:
    def __init__(self, status_code=200, content=b"", json_data=None):
        self.status_code = status_code
        self.content = content
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeGooglePlayAPI:
    def __init__(self, locale="en_US", timezone="UTC", device_codename="bacon"):
        self.locale = locale
        self.timezone = timezone
        self.device_codename = device_codename
        self.checked_in = False
        self.logged_in = False
        self.toc_loaded = False
        self.device_uploaded = False

    def checkin(self, email, auth_token):
        self.checked_in = True
        return int("1234", 16)

    def login(self, authSubToken=None, gsfId=None):
        self.logged_in = bool(authSubToken and gsfId is not None)

    def toc(self):
        self.toc_loaded = True

    def uploadDeviceConfig(self):
        self.device_uploaded = True

    def details(self, package_name):
        return {
            "title": "Example App",
            "details": {
                "appDetails": {
                    "versionCode": 42,
                    "versionString": "1.2.3",
                }
            },
        }

    def getHeaders(self):
        return {"User-Agent": "test-agent"}


def _build_fake_gp(from_string):
    return SimpleNamespace(
        GooglePlayAPI=_FakeGooglePlayAPI,
        PURCHASE_URL="https://purchase.local",
        DELIVERY_URL="https://delivery.local",
        googleplay_pb2=SimpleNamespace(
            ResponseWrapper=SimpleNamespace(FromString=staticmethod(from_string))
        ),
    )


def test_aurora_get_latest_version_uses_dispenser_and_caches_version_code():
    fake_gp = _build_fake_gp(lambda _payload: _Proto())

    with (
        patch.object(aurora_module, "gp", fake_gp),
        patch.object(
            aurora_module.requests,
            "get",
            return_value=_Response(
                json_data={"email": "anon@example.com", "auth": "token-value"}
            ),
        ),
    ):
        source = aurora_module.AuroraSource()
        version, release_url, title = source.get_latest_version("com.example.app")

    assert version == "1.2.3"
    assert release_url == "com.example.app"
    assert title == "Example App"
    assert source._version_code_by_package["com.example.app"] == 42
    assert source._authenticated is True


def test_aurora_get_download_url_uses_purchase_and_delivery():
    def from_string(payload: bytes):
        if payload == b"purchase":
            buy_response = _Proto(downloadToken="delivery-token")
            return _Proto(
                commands=_Proto(displayErrorMessage=""),
                payload=_Proto(buyResponse=buy_response),
            )

        if payload == b"delivery":
            app_delivery_data = _Proto(downloadUrl="https://example.com/app.apk")
            delivery_response = _Proto(appDeliveryData=app_delivery_data)
            return _Proto(
                commands=_Proto(displayErrorMessage=""),
                payload=_Proto(deliveryResponse=delivery_response),
            )

        raise AssertionError("Unexpected payload marker")

    fake_gp = _build_fake_gp(from_string)

    def fake_post(url, headers=None, params=None, timeout=None):
        assert url == fake_gp.PURCHASE_URL
        assert params["doc"] == "com.example.app"
        assert params["vc"] == "42"
        return _Response(content=b"purchase")

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url == fake_gp.DELIVERY_URL
        assert params["dtok"] == "delivery-token"
        return _Response(content=b"delivery")

    with (
        patch.object(aurora_module, "gp", fake_gp),
        patch.object(aurora_module.requests, "post", side_effect=fake_post),
        patch.object(aurora_module.requests, "get", side_effect=fake_get),
    ):
        source = aurora_module.AuroraSource()
        source._authenticated = True
        source._version_code_by_package["com.example.app"] = 42

        download_url = source.get_download_url("com.example.app")

    assert download_url == "https://example.com/app.apk"
