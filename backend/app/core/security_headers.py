from starlette.types import ASGIApp, Receive, Scope, Send

# Swagger UI (/docs) and ReDoc (/redoc) load their JS/CSS from a CDN and
# inline-execute -- a locked-down CSP would otherwise break them. Every other
# route on this API only ever returns JSON, so `default-src 'none'` is safe
# everywhere else.
_UNRESTRICTED_CSP_PATHS = {"/docs", "/redoc", "/openapi.json"}

_CSP = "default-src 'none'; frame-ancestors 'none'"

_STATIC_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"geolocation=(), camera=(), microphone=()"),
    # Ignored by browsers on plain-HTTP responses (RFC 6797) -- safe to send
    # unconditionally rather than branching on ENVIRONMENT/scheme.
    (b"strict-transport-security", b"max-age=63072000; includeSubDomains"),
)


class SecurityHeadersMiddleware:
    """Adds standard defensive response headers to every HTTP response.
    Implemented as a plain ASGI middleware (not BaseHTTPMiddleware) so it
    never buffers streaming responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(_STATIC_HEADERS)
                if path not in _UNRESTRICTED_CSP_PATHS:
                    headers.append((b"content-security-policy", _CSP.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
