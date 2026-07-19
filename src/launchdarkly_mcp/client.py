import os
import httpx
from typing import Any


class LDClient:
    def __init__(self):
        api_key = os.environ.get("LD_API_KEY")
        if not api_key:
            raise ValueError(
                "LD_API_KEY environment variable is required. "
                "Create a personal access token at: "
                "https://app.launchdarkly.com/settings/authorization"
            )
        self.api_key = api_key
        self.base = "https://app.launchdarkly.com/api/v2"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with httpx.Client() as c:
            r = c.get(f"{self.base}{path}", headers=self.headers, params=params)
            r.raise_for_status()
            return r.json()

    def _patch(self, path: str, body: list[dict[str, Any]]) -> dict[str, Any]:
        with httpx.Client() as c:
            r = c.patch(f"{self.base}{path}", headers=self.headers, json=body)
            r.raise_for_status()
            return r.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client() as c:
            r = c.post(f"{self.base}{path}", headers=self.headers, json=body)
            r.raise_for_status()
            return r.json()

    def list_projects(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._get("/projects", {"limit": min(limit, 50), "offset": offset})

    def list_flags(
        self,
        project_key: str,
        env_key: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": min(limit, 50), "offset": offset}
        if env_key:
            params["env"] = env_key
        return self._get(f"/flags/{project_key}", params)

    def get_flag(self, project_key: str, flag_key: str) -> dict[str, Any]:
        return self._get(f"/flags/{project_key}/{flag_key}")

    def get_environments(self, project_key: str) -> dict[str, Any]:
        return self._get(f"/projects/{project_key}/environments")

    def search_audit_log(
        self,
        filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": min(limit, 50), "offset": offset}
        if filter:
            params["filter"] = filter
        return self._get("/auditlog", params)

    def get_flag_status(
        self, project_key: str, flag_key: str, env_key: str
    ) -> dict[str, Any]:
        flag = self.get_flag(project_key, flag_key)
        env_data = flag.get("environments", {}).get(env_key, {})
        return {
            "key": flag_key,
            "project": project_key,
            "environment": env_key,
            "on": env_data.get("on", False),
            "archived": flag.get("archived", False),
            "temporary": flag.get("temporary", False),
            "tags": flag.get("tags", []),
            "version": env_data.get("version"),
        }

    def toggle_flag(
        self, project_key: str, flag_key: str, env_key: str, on: bool
    ) -> dict[str, Any]:
        patch = [
            {
                "op": "replace",
                "path": f"/environments/{env_key}/on",
                "value": on,
            }
        ]
        return self._patch(f"/flags/{project_key}/{flag_key}", patch)

    def patch_flag(
        self, project_key: str, flag_key: str, operations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return self._patch(f"/flags/{project_key}/{flag_key}", operations)

    def create_flag(
        self,
        project_key: str,
        name: str,
        key: str,
        description: str = "",
        temporary: bool = True,
        variations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if variations is None:
            variations = [
                {"name": "On", "value": True, "description": "Enabled"},
                {"name": "Off", "value": False, "description": "Disabled"},
            ]
        body: dict[str, Any] = {
            "name": name,
            "key": key,
            "variations": variations,
            "temporary": temporary,
        }
        if description:
            body["description"] = description
        return self._post(f"/flags/{project_key}", body)

    def get_flag_prerequisites(
        self, project_key: str, flag_key: str
    ) -> dict[str, Any]:
        flag = self.get_flag(project_key, flag_key)
        return {
            "flag_key": flag_key,
            "project_key": project_key,
            "prerequisites": flag.get("prerequisites", []),
        }
