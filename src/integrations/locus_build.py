"""Locus Build integration — deploy Vigil to Railway via Locus API.

Enables autonomous deployment: push code to GitHub, deploy to Railway,
all paid through the Locus wallet in USDC.
"""

import httpx
import logging
from typing import Optional
from src.config import get_settings

logger = logging.getLogger(__name__)

LOCUS_API = "https://beta-api.paywithlocus.com/api"


class LocusBuildClient:
    """Deploy and manage Vigil on Railway via Locus Build API."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.locus_api_key
        self._client = httpx.AsyncClient(
            base_url=LOCUS_API,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    async def get_build_docs(self) -> str:
        """Fetch the full Locus Build API documentation."""
        resp = await self._client.get("/apps/md")
        resp.raise_for_status()
        return resp.text

    async def create_project(self, name: str = "vigil") -> dict:
        """Create a new Railway project via Locus Build."""
        resp = await self._client.post(
            "/apps/projects",
            json={"name": name, "description": "Vigil — Behavioral intelligence for agent wallets"},
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    async def deploy_from_github(
        self,
        project_id: str,
        repo: str = "Alfaxad/Vigil",
        branch: str = "main",
    ) -> dict:
        """Deploy Vigil from GitHub repo to Railway."""
        resp = await self._client.post(
            f"/apps/projects/{project_id}/services",
            json={
                "name": "vigil-web",
                "source": {"type": "github", "repo": repo, "branch": branch},
                "builder": "dockerfile",
                "env": {
                    "PORT": "8080",
                },
            },
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    async def close(self):
        await self._client.aclose()
