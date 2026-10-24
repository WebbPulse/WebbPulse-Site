"""Fixtures for the post-deploy smoke of the company site.

The reusable e2e workflow sets the `E2E_*` variables. The site is static, so the suite
needs only its origin, its www host and, on staging, a minted access gate session. The
gate cookies come from `webbpulse.e2e.gate`, which reads the signing key from SSM itself
so the key never reaches the workflow or a test report.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from urllib.parse import urlsplit

import httpx
import pytest

from tests.target import SiteTarget


@pytest.fixture(scope="session")
def site() -> SiteTarget:
    """The deployed site, read from `E2E_WEB_BASE_URL` and `E2E_ENVIRONMENT`."""
    origin = os.environ["E2E_WEB_BASE_URL"].rstrip("/")
    host = urlsplit(origin).hostname or ""
    environment = os.environ.get("E2E_ENVIRONMENT", "staging")
    portfolio = "portfolio.webbpulse.com" if environment == "production" else "staging.portfolio.webbpulse.com"
    return SiteTarget(
        environment=environment,
        origin=origin,
        host=host,
        www_host=f"www.{host}",
        portfolio_origin=f"https://{portfolio}",
    )


@pytest.fixture(scope="session")
def gate_cookie_values(site: SiteTarget) -> dict[str, str]:
    """Minted access gate cookies on staging, an empty mapping where there is no gate."""
    parameter = os.environ.get("E2E_GATE_SIGNING_KEY_SSM_PARAMETER", "")
    if not parameter:
        return {}
    import boto3
    from webbpulse.e2e.gate import mint_gate_cookies

    cookies = mint_gate_cookies(
        ssm_client=boto3.session.Session(region_name=os.environ.get("E2E_AWS_REGION", "us-west-2")).client("ssm"),
        parameter_name=parameter,
        key_pair_id=os.environ["E2E_GATE_KEY_PAIR_ID"],
        domain=os.environ["E2E_GATE_COOKIE_DOMAIN"],
        environment=site.environment,
    )
    return dict(cookies.as_httpx_cookies())


@pytest.fixture(scope="session")
def http(gate_cookie_values: dict[str, str]) -> Iterator[httpx.Client]:
    """A client that never follows redirects and sends the gate session when there is one."""
    headers = {"cookie": "; ".join(f"{name}={value}" for name, value in gate_cookie_values.items())}
    with httpx.Client(follow_redirects=False, timeout=20.0, headers=headers if gate_cookie_values else None) as client:
        yield client
