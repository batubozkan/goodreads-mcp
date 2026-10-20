"""Streamable HTTP entry point, for hosting the server in a container.

The stdio server in server.py is unchanged; this wraps the same FastMCP
instance and serves it at http://HOST:PORT/mcp.

    GOODREADS_MCP_HOST           bind address (default 0.0.0.0)
    GOODREADS_MCP_PORT           port (default 8000)
    GOODREADS_MCP_ALLOWED_HOSTS  comma-separated Host header allowlist, e.g.
                                 "goodreads-mcp.example.com,192.168.1.21:*".
                                 Empty disables the DNS rebinding check.

The server has no auth of its own: put it behind a proxy that does.
"""

from __future__ import annotations

import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .server import mcp


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def main() -> None:
    allowed = [h.strip() for h in os.environ.get("GOODREADS_MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
    mcp.settings.host = os.environ.get("GOODREADS_MCP_HOST", "0.0.0.0")
    mcp.settings.port = int(os.environ.get("GOODREADS_MCP_PORT", "8000"))
    # Stateless JSON responses: each request stands alone, so a proxy or
    # container restart never strands a client on a dead session id.
    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    # FastMCP turns on the DNS rebinding check for its default 127.0.0.1 host
    # at construction time; replace it, or every proxied request gets a 421.
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=bool(allowed),
        allowed_hosts=allowed,
    )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
