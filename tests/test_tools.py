import json
import os

import httpx
import pytest
import respx

from launchdarkly_mcp.client import LDClient

BASE = "https://app.launchdarkly.com/api/v2"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _set_env():
    os.environ["LD_API_KEY"] = "test-api-key"
    yield
    del os.environ["LD_API_KEY"]


@pytest.fixture
def client() -> LDClient:
    return LDClient()


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------


@respx.mock
def test_list_projects(client: LDClient):
    route = respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"key": "default", "name": "Default Project"},
                ]
            },
        )
    )

    result = client.list_projects(limit=20, offset=0)

    assert result["items"][0]["key"] == "default"
    assert route.called


# ---------------------------------------------------------------------------
# get_flag
# ---------------------------------------------------------------------------


@respx.mock
def test_get_flag(client: LDClient):
    respx.get(f"{BASE}/flags/default/my-flag").mock(
        return_value=httpx.Response(
            200,
            json={
                "key": "my-flag",
                "name": "My Flag",
                "environments": {
                    "production": {"on": True, "version": 42},
                },
            },
        )
    )

    result = client.get_flag("default", "my-flag")

    assert result["key"] == "my-flag"
    assert result["environments"]["production"]["on"] is True


# ---------------------------------------------------------------------------
# get_flag_status
# ---------------------------------------------------------------------------


@respx.mock
def test_get_flag_status(client: LDClient):
    respx.get(f"{BASE}/flags/default/my-flag").mock(
        return_value=httpx.Response(
            200,
            json={
                "key": "my-flag",
                "name": "My Flag",
                "archived": False,
                "temporary": True,
                "tags": ["frontend"],
                "environments": {
                    "production": {"on": True, "version": 5},
                },
            },
        )
    )

    result = client.get_flag_status("default", "my-flag", "production")

    assert result["on"] is True
    assert result["environment"] == "production"
    assert result["archived"] is False


# ---------------------------------------------------------------------------
# toggle_flag
# ---------------------------------------------------------------------------


@respx.mock
def test_toggle_flag(client: LDClient):
    respx.patch(f"{BASE}/flags/default/my-flag").mock(
        return_value=httpx.Response(
            200, json={"key": "my-flag", "name": "My Flag"}
        )
    )

    result = client.toggle_flag("default", "my-flag", "production", True)

    assert result["key"] == "my-flag"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@respx.mock
def test_list_projects_unauthorized(client: LDClient):
    respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.list_projects()


# ---------------------------------------------------------------------------
# Tool-level error formatting
# ---------------------------------------------------------------------------


@respx.mock
def test_error_formatting_in_tools():
    from launchdarkly_mcp.tools import list_projects, _format_error

    respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(403, json={"message": "Forbidden"})
    )

    result = list_projects(limit=5)

    assert "Error 403" in result
    assert "Forbidden" in result


# ---------------------------------------------------------------------------
# search_audit_log
# ---------------------------------------------------------------------------


@respx.mock
def test_search_audit_log_with_flag_filter(client: LDClient):
    route = respx.get(f"{BASE}/auditlog").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "title": "Updated flag",
                        "member": {"email": "user@example.com"},
                    }
                ]
            },
        )
    )

    result = client.search_audit_log("resource.key:my-flag", limit=10)

    assert result["items"][0]["member"]["email"] == "user@example.com"
    assert route.called
