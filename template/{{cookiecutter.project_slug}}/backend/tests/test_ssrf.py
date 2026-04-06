"""Tests for SSRF protection in webhook URL validation.

Covers validate_webhook_url() and _is_ip_blocked() from app.core.sanitize.
"""

from unittest.mock import patch

import pytest

# Import directly — this module has no dependencies on database/framework code.
import sys
import os

# The sanitize module lives inside the Jinja template tree, but it is plain
# Python with no cookiecutter variables, so we can import it directly by
# adding its parent to sys.path.
_SANITIZE_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    "app",
    "core",
)
sys.path.insert(0, os.path.normpath(_SANITIZE_DIR))

from sanitize import (  # noqa: E402
    SSRFBlockedError,
    _is_ip_blocked,
    validate_webhook_url,
)


# ---------------------------------------------------------------------------
# _is_ip_blocked
# ---------------------------------------------------------------------------


class TestIsIpBlocked:
    """Tests for the _is_ip_blocked helper."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.1.1",
            "169.254.169.254",
            "0.0.0.0",
            "::1",
            "fe80::1",
            "fc00::1",
        ],
    )
    def test_blocked_ips(self, ip: str):
        assert _is_ip_blocked(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "8.8.8.8",
            "1.1.1.1",
            "93.184.216.34",  # example.com
            "2606:4700:4700::1111",  # Cloudflare public DNS IPv6
        ],
    )
    def test_allowed_ips(self, ip: str):
        assert _is_ip_blocked(ip) is False

    def test_unparseable_ip_is_blocked(self):
        """If we can't parse it, we block it (fail-closed)."""
        assert _is_ip_blocked("not-an-ip") is True


# ---------------------------------------------------------------------------
# validate_webhook_url — scheme validation
# ---------------------------------------------------------------------------


class TestSchemeValidation:
    """Blocked schemes must raise SSRFBlockedError."""

    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "ftp://mirror.example.com/pub",
            "gopher://evil.com/",
            "data:text/html,<h1>hi</h1>",
        ],
    )
    def test_blocked_schemes(self, url: str):
        with pytest.raises(SSRFBlockedError):
            validate_webhook_url(url)

    def test_empty_scheme_is_rejected(self):
        with pytest.raises((SSRFBlockedError, ValueError)):
            validate_webhook_url("://example.com/hook")


# ---------------------------------------------------------------------------
# validate_webhook_url — IP-literal URLs
# ---------------------------------------------------------------------------


class TestDirectIpUrls:
    """URLs with IP-address hostnames (no DNS involved)."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/hook",
            "https://169.254.169.254/latest/meta-data/",
            "http://10.0.0.1:8080/callback",
            "http://192.168.1.1/hook",
            "http://[::1]/hook",
            "http://0.0.0.0/hook",
        ],
    )
    def test_private_ip_blocked(self, url: str):
        with pytest.raises(SSRFBlockedError):
            validate_webhook_url(url)

    def test_public_ip_allowed(self):
        """A public IP should pass validation (DNS resolution is skipped)."""
        url = "https://93.184.216.34/webhook"
        assert validate_webhook_url(url) == url


# ---------------------------------------------------------------------------
# validate_webhook_url — DNS resolution to private IP
# ---------------------------------------------------------------------------


class TestDnsResolution:
    """DNS resolving to a private IP must be blocked."""

    def _mock_getaddrinfo_private(self, *args, **kwargs):
        """Return a private IP for any hostname."""
        return [
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]

    def _mock_getaddrinfo_public(self, *args, **kwargs):
        """Return a public IP for any hostname."""
        return [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]

    def test_dns_resolves_to_private_ip(self):
        with patch("sanitize.socket.getaddrinfo", self._mock_getaddrinfo_private):
            with pytest.raises(SSRFBlockedError):
                validate_webhook_url("https://evil.attacker.com/hook")

    def test_dns_resolves_to_public_ip(self):
        with patch("sanitize.socket.getaddrinfo", self._mock_getaddrinfo_public):
            result = validate_webhook_url("https://example.com/webhook")
            assert result == "https://example.com/webhook"


# ---------------------------------------------------------------------------
# validate_webhook_url — edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases: empty URL, missing hostname, credentials in URL."""

    def test_empty_url(self):
        with pytest.raises((SSRFBlockedError, ValueError)):
            validate_webhook_url("")

    def test_no_hostname(self):
        with pytest.raises(ValueError):
            validate_webhook_url("https:///path")

    def test_url_with_credentials_rejected(self):
        """URLs with userinfo (user:pass@) should be rejected."""
        with pytest.raises(SSRFBlockedError):
            validate_webhook_url("http://user:pass@internal.example.com/hook")

    def test_url_with_username_only_rejected(self):
        with pytest.raises(SSRFBlockedError):
            validate_webhook_url("http://admin@169.254.169.254/")

    def test_allowed_https_url(self):
        """A normal public URL should pass (mock DNS to avoid network calls)."""
        with patch(
            "sanitize.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ):
            result = validate_webhook_url("https://example.com/webhook")
            assert result == "https://example.com/webhook"

    def test_allowed_http_url(self):
        """An http:// URL to a public IP should also pass."""
        with patch(
            "sanitize.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 80))],
        ):
            result = validate_webhook_url("http://example.com/webhook")
            assert result == "http://example.com/webhook"


# ---------------------------------------------------------------------------
# SSRFBlockedError is a subclass of ValueError
# ---------------------------------------------------------------------------


class TestSSRFBlockedError:
    """The dedicated exception type preserves backward compatibility."""

    def test_is_value_error_subclass(self):
        assert issubclass(SSRFBlockedError, ValueError)

    def test_catchable_as_value_error(self):
        with pytest.raises(ValueError):
            raise SSRFBlockedError("blocked")
