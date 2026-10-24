"""The deployed site under test."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiteTarget:
    """Where the deployed site lives and which hosts it answers on."""

    environment: str
    origin: str
    host: str
    www_host: str
    portfolio_origin: str
