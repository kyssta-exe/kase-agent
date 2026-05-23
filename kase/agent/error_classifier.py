"""Centralized API error classification for failover decisions."""

from enum import Enum
from typing import Optional


class FailoverReason(Enum):
    AUTH_ERROR = "auth_error"
    BILLING_ERROR = "billing_error"
    RATE_LIMITED = "rate_limited"
    OVERLOADED = "overloaded"
    TIMEOUT = "timeout"
    CONTEXT_OVERFLOW = "context_overflow"
    IMAGE_TOO_LARGE = "image_too_large"
    BAD_GATEWAY = "bad_gateway"
    SERVER_ERROR = "server_error"
    CONTENT_FILTERED = "content_filtered"
    UNKNOWN = "unknown"
    NONE = "none"


def classify_api_error(error: Exception, provider: str = "") -> FailoverReason:
    err_str = str(error).lower()
    status = getattr(error, "status_code", 0) or getattr(error, "code", 0)
    
    if status == 401 or "unauthorized" in err_str or "authentication" in err_str:
        return FailoverReason.AUTH_ERROR
    if status == 402 or "billing" in err_str or "quota" in err_str or "insufficient" in err_str:
        return FailoverReason.BILLING_ERROR
    if status == 429 or "rate limit" in err_str or "too many requests" in err_str:
        return FailoverReason.RATE_LIMITED
    if status == 503 or status == 502 or "overloaded" in err_str or "service unavailable" in err_str:
        return FailoverReason.OVERLOADED
    if status == 504 or "timeout" in err_str or "timed out" in err_str:
        return FailoverReason.TIMEOUT
    if "context_length" in err_str or "maximum context" in err_str or "too many tokens" in err_str:
        return FailoverReason.CONTEXT_OVERFLOW
    if "image" in err_str and ("size" in err_str or "large" in err_str):
        return FailoverReason.IMAGE_TOO_LARGE
    if status >= 500:
        return FailoverReason.SERVER_ERROR
    if "content_filter" in err_str or "safety" in err_str:
        return FailoverReason.CONTENT_FILTERED
    
    return FailoverReason.UNKNOWN


def should_retry(reason: FailoverReason) -> bool:
    return reason in {
        FailoverReason.RATE_LIMITED, FailoverReason.OVERLOADED,
        FailoverReason.TIMEOUT, FailoverReason.SERVER_ERROR,
        FailoverReason.BAD_GATEWAY,
    }


def should_fallback(reason: FailoverReason) -> bool:
    return reason in {
        FailoverReason.AUTH_ERROR, FailoverReason.BILLING_ERROR,
        FailoverReason.CONTEXT_OVERFLOW, FailoverReason.UNKNOWN,
    }
