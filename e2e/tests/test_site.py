"""Smoke checks that the deployed company site serves the page and its edge rules."""

from __future__ import annotations

import httpx

from tests.target import SiteTarget


def test_home_page_serves_the_landing_page(http: httpx.Client, site: SiteTarget) -> None:
    """The apex answers 200 with the prerendered landing page."""
    response = http.get(f"{site.origin}/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "WebbPulse" in response.text


def test_home_page_sends_the_security_headers(http: httpx.Client, site: SiteTarget) -> None:
    """The response headers policy enforces the content security policy and HSTS."""
    response = http.get(f"{site.origin}/")
    assert "default-src 'self'" in response.headers.get("content-security-policy", "")
    assert "max-age=" in response.headers.get("strict-transport-security", "")
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_static_files_are_served(http: httpx.Client, site: SiteTarget) -> None:
    """Files with an extension pass through to the bucket."""
    for path in ("/robots.txt", "/favicon.svg"):
        assert http.get(f"{site.origin}{path}").status_code == 200, path


def test_www_redirects_to_the_apex(http: httpx.Client, site: SiteTarget) -> None:
    """The www host sends a permanent redirect to the apex, keeping the path and query."""
    response = http.get(f"https://{site.www_host}/some/path?a=1")
    assert response.status_code == 301
    assert response.headers["location"] == f"{site.origin}/some/path?a=1"


def test_old_portfolio_paths_redirect_to_the_portfolio(http: httpx.Client, site: SiteTarget) -> None:
    """Paths the portfolio served on this host before it moved go to the portfolio host."""
    response = http.get(f"{site.origin}/blog/a-post")
    assert response.status_code == 301
    assert response.headers["location"] == f"{site.portfolio_origin}/blog/a-post"


def test_unknown_pages_answer_404(http: httpx.Client, site: SiteTarget) -> None:
    """Any other extensionless path is a 404 page, not the landing page."""
    response = http.get(f"{site.origin}/no-such-page")
    assert response.status_code == 404
    assert "Page not found" in response.text
