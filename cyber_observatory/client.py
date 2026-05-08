from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ApiClient:
    base_url: str
    token: str | None = None

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, email: str, password: str) -> str:
        res = httpx.post(
            f"{self.base_url}/api/auth/token",
            json={"email": email, "password": password},
            timeout=20.0,
        )
        res.raise_for_status()
        token = res.json()["access_token"]
        self.token = token
        return token

    def health(self) -> dict[str, Any]:
        res = httpx.get(f"{self.base_url}/api/health", timeout=15.0)
        res.raise_for_status()
        return res.json()

    def stats(self) -> dict[str, Any]:
        res = httpx.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=self._headers(),
            timeout=20.0,
        )
        res.raise_for_status()
        return res.json()

    def records(self, department_id: int | None = None) -> list[dict[str, Any]]:
        params = {"department_id": department_id} if department_id else None
        res = httpx.get(
            f"{self.base_url}/api/compliance/records",
            headers=self._headers(),
            params=params,
            timeout=20.0,
        )
        res.raise_for_status()
        return list(res.json())

    def controls(self, framework_id: int | None = None) -> list[dict[str, Any]]:
        params = {"framework_id": framework_id} if framework_id else None
        res = httpx.get(
            f"{self.base_url}/api/controls",
            headers=self._headers(),
            params=params,
            timeout=20.0,
        )
        res.raise_for_status()
        return list(res.json())

    def frameworks(self) -> list[dict[str, Any]]:
        res = httpx.get(
            f"{self.base_url}/api/controls/frameworks",
            headers=self._headers(),
            timeout=20.0,
        )
        res.raise_for_status()
        return list(res.json())

    def departments(self) -> list[dict[str, Any]]:
        res = httpx.get(
            f"{self.base_url}/api/departments",
            headers=self._headers(),
            timeout=20.0,
        )
        res.raise_for_status()
        return list(res.json())

    def create_department(self, name_ar: str, name_en: str, code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name_ar": name_ar, "name_en": name_en}
        if code:
            payload["code"] = code
        res = httpx.post(
            f"{self.base_url}/api/departments",
            headers=self._headers(),
            json=payload,
            timeout=20.0,
        )
        res.raise_for_status()
        return dict(res.json())

    def patch_record(self, record_id: int, status: str) -> dict[str, Any]:
        res = httpx.patch(
            f"{self.base_url}/api/compliance/records/{record_id}",
            headers=self._headers(),
            json={"status": status},
            timeout=20.0,
        )
        res.raise_for_status()
        return dict(res.json())

    def gap_analysis(self) -> dict[str, Any]:
        res = httpx.post(
            f"{self.base_url}/api/ai/gap-analysis",
            headers=self._headers(),
            json={},
            timeout=35.0,
        )
        res.raise_for_status()
        return res.json()

    def explain_framework(self, framework_id: int) -> dict[str, Any]:
        res = httpx.post(
            f"{self.base_url}/api/ai/explain-framework",
            headers=self._headers(),
            json={"framework_id": framework_id},
            timeout=35.0,
        )
        res.raise_for_status()
        return dict(res.json())

    def analyze_file(self, file_name: str, file_bytes: bytes, focus: str | None = None) -> dict[str, Any]:
        files = {"file": (file_name, file_bytes)}
        data = {"focus": focus} if focus else None
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        res = httpx.post(
            f"{self.base_url}/api/ai/analyze-file",
            headers=headers,
            files=files,
            data=data,
            timeout=60.0,
        )
        res.raise_for_status()
        return dict(res.json())

    def download_compliance_pdf(self, department_id: int | None = None, framework_id: int | None = None) -> bytes:
        params: dict[str, Any] = {}
        if department_id is not None:
            params["department_id"] = department_id
        if framework_id is not None:
            params["framework_id"] = framework_id
        res = httpx.get(
            f"{self.base_url}/api/reports/compliance.pdf",
            headers=self._headers(),
            params=params,
            timeout=60.0,
        )
        res.raise_for_status()
        return res.content

    def chat(self, message: str) -> dict[str, Any]:
        res = httpx.post(
            f"{self.base_url}/api/ai/chat",
            headers=self._headers(),
            json={"message": message},
            timeout=35.0,
        )
        res.raise_for_status()
        return res.json()

