import json

from fastmcp import FastMCP

from launchdarkly_mcp.client import LDClient

mcp = FastMCP("launchdarkly-mcp")
ld = LDClient()


def _to_json(data) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def list_projects(limit: int = 20, offset: int = 0) -> str:
    """List all projects in the LaunchDarkly account.

    Args:
        limit: Maximum number of projects to return (max 50, default 20)
        offset: Number of projects to skip for pagination (default 0)
    """
    try:
        return _to_json(ld.list_projects(limit, offset))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def list_flags(
    project_key: str, env_key: str | None = None, limit: int = 20, offset: int = 0
) -> str:
    """List all feature flags in a project, optionally filtered by environment.

    Args:
        project_key: The project key (e.g. 'default')
        env_key: Optional environment filter (e.g. 'production')
        limit: Maximum number of flags to return (max 50, default 20)
        offset: Number of flags to skip for pagination (default 0)
    """
    try:
        return _to_json(ld.list_flags(project_key, env_key, limit, offset))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def get_flag(project_key: str, flag_key: str) -> str:
    """Get detailed configuration for a specific feature flag, including targeting rules.

    Args:
        project_key: The project key (e.g. 'default')
        flag_key: The feature flag key (e.g. 'my-feature-flag')
    """
    try:
        return _to_json(ld.get_flag(project_key, flag_key))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def get_environments(project_key: str) -> str:
    """List all environments for a project.

    Args:
        project_key: The project key (e.g. 'default')
    """
    try:
        return _to_json(ld.get_environments(project_key))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def search_audit_log(
    filter: str | None = None,
    flag_key: str | None = None,
    days_back: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search the LaunchDarkly audit log for changes.

    Provide either a raw LD filter string, or use convenience params.
    LD filter grammar examples:
      kind:flag                                          — flag changes only
      date:after(2024-01-01)ANDdate:before(2024-12-31)   — date range
      resource.key:my-flag-key                            — changes to a specific flag

    Args:
        filter: Raw LD filter string (overrides flag_key and days_back if set)
        flag_key: Convenience filter — only show changes for this flag key
        days_back: Convenience filter — only show changes from last N days
        limit: Maximum entries to return (max 50, default 20)
        offset: Number of entries to skip for pagination (default 0)
    """
    try:
        built_filter = filter
        if not built_filter:
            parts = []
            if flag_key:
                parts.append(f"resource.key:{flag_key}")
            if days_back is not None:
                from datetime import datetime, timedelta, timezone
                after = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                parts.append(f"date:after({after})")
            if parts:
                built_filter = "AND".join(parts)
        return _to_json(ld.search_audit_log(built_filter, limit, offset))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def get_flag_status(project_key: str, flag_key: str, env_key: str) -> str:
    """Check whether a feature flag is on or off in a specific environment.

    Args:
        project_key: The project key (e.g. 'default')
        flag_key: The feature flag key (e.g. 'my-feature-flag')
        env_key: The environment key (e.g. 'production')
    """
    try:
        return _to_json(ld.get_flag_status(project_key, flag_key, env_key))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def toggle_flag(project_key: str, flag_key: str, env_key: str, on: bool) -> str:
    """Turn a feature flag on or off in a specific environment.

    Uses JSON Patch (RFC 6902) to update the flag's targeting switch.

    Args:
        project_key: The project key (e.g. 'default')
        flag_key: The feature flag key (e.g. 'my-feature-flag')
        env_key: The environment key (e.g. 'production')
        on: Whether the flag should be enabled (true) or disabled (false)
    """
    try:
        return _to_json(ld.toggle_flag(project_key, flag_key, env_key, on))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def update_flag_targeting(
    project_key: str,
    flag_key: str,
    env_key: str,
    context_kind: str = "user",
    user_keys: str = "",
    variation: int = 0,
    action: str = "add",
) -> str:
    """Add or remove user/context keys from flag targeting for a specific variation.

    For 'add': appends the user key to the contextTargets values array.
    For 'remove': fetches current targeting to locate the key, then removes it.

    Args:
        project_key: The project key (e.g. 'default')
        flag_key: The feature flag key (e.g. 'my-feature-flag')
        env_key: The environment key (e.g. 'production')
        context_kind: Context kind (default 'user')
        user_keys: Comma-separated list of user/context keys to add or remove
        variation: Variation index (default 0)
        action: 'add' or 'remove'
    """
    try:
        keys = [k.strip() for k in user_keys.split(",") if k.strip()]
        if not keys:
            return "Error: user_keys must not be empty"

        if action == "add":
            flag = ld.get_flag(project_key, flag_key)
            env = flag.get("environments", {}).get(env_key, {})
            targets = env.get("contextTargets", env.get("targets", []))
            operations = []
            for key in keys:
                target_idx = None
                for ti, t in enumerate(targets):
                    kind_matches = (
                        t.get("contextKind") == context_kind
                        or (not t.get("contextKind") and context_kind == "user")
                    )
                    if kind_matches and t.get("variation") == variation:
                        target_idx = ti
                        break
                if target_idx is not None:
                    operations.append({
                        "op": "add",
                        "path": f"/environments/{env_key}/contextTargets/{target_idx}/values/-",
                        "value": key,
                    })
                else:
                    operations.append({
                        "op": "add",
                        "path": f"/environments/{env_key}/contextTargets/-",
                        "value": {
                            "contextKind": context_kind,
                            "values": [key],
                            "variation": variation,
                        },
                    })
            return _to_json(ld.patch_flag(project_key, flag_key, operations))

        elif action == "remove":
            flag = ld.get_flag(project_key, flag_key)
            env = flag.get("environments", {}).get(env_key, {})
            targets = env.get("contextTargets", env.get("targets", []))
            operations = []
            for key in keys:
                found = False
                for ti, t in enumerate(targets):
                    if (
                        t.get("contextKind") == context_kind
                        or context_kind == "user"
                    ) and t.get("variation") == variation:
                        if key in t.get("values", []):
                            vi = t["values"].index(key)
                            operations.append(
                                {
                                    "op": "remove",
                                    "path": (
                                        f"/environments/{env_key}"
                                        f"/contextTargets/{ti}/values/{vi}"
                                    ),
                                }
                            )
                            found = True
                            break
                if not found:
                    return f"Error: key '{key}' not found in {context_kind} targeting for variation {variation}"
            return _to_json(ld.patch_flag(project_key, flag_key, operations))
        else:
            return f"Error: action must be 'add' or 'remove', got '{action}'"

    except Exception as e:
        return _format_error(e)


@mcp.tool()
def create_flag(
    project_key: str,
    name: str,
    key: str,
    description: str = "",
    temporary: bool = True,
) -> str:
    """Create a new feature flag skeleton in a project.

    Creates a boolean flag with On/Off variations by default.

    Args:
        project_key: The project key (e.g. 'default')
        name: A human-readable name for the flag (e.g. 'My Feature Flag')
        key: A unique flag key (e.g. 'my-feature-flag')
        description: Optional description of the flag
        temporary: Whether the flag is temporary (default true)
    """
    try:
        return _to_json(ld.create_flag(project_key, name, key, description, temporary))
    except Exception as e:
        return _format_error(e)


@mcp.tool()
def get_flag_prerequisites(project_key: str, flag_key: str) -> str:
    """Check what prerequisites (dependencies) a feature flag has.

    Prerequisites are other flags that must be on for this flag to evaluate.

    Args:
        project_key: The project key (e.g. 'default')
        flag_key: The feature flag key (e.g. 'my-feature-flag')
    """
    try:
        return _to_json(ld.get_flag_prerequisites(project_key, flag_key))
    except Exception as e:
        return _format_error(e)


def _format_error(e: Exception) -> str:
    if hasattr(e, "response"):
        resp = getattr(e, "response")
        try:
            detail = resp.json()
            message = detail.get("message", resp.text)
        except Exception:
            message = resp.text[:500]
        return f"Error {resp.status_code}: {message}"
    return f"Error: {e}"
