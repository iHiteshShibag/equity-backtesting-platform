from contextvars import ContextVar

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

# Set by app.modules.auth.deps.get_current_user (which runs, as a FastAPI
# dependency, before slowapi's own rate-limit check on the same request) so
# org_tier_rate_limit below can see the caller's tier. slowapi's dynamic-limit
# callables don't receive the Request object directly -- only a `key` derived
# from key_func -- so a contextvar is the simplest way to thread this through.
current_user_org_tier: ContextVar[str | None] = ContextVar("current_user_org_tier", default=None)


def org_tier_rate_limit(key: str) -> str:
    """Dynamic rate-limit string for @limiter.limit(), keyed on the caller's
    organization tier (see app/modules/orgs/models.py TIER_RATE_LIMITS).
    Falls back to the free tier if no tier was resolved (e.g. auth failed
    upstream -- the endpoint's own auth dependency still rejects the request)."""
    from app.modules.orgs.models import TIER_RATE_LIMITS

    tier = current_user_org_tier.get() or "free"
    return TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["free"])
