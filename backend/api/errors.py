from __future__ import annotations

from dataclasses import dataclass


@dataclass
class APIError(Exception):
    status_code: int
    error: str
    message: str


def not_found(message: str) -> APIError:
    return APIError(
        status_code=404,
        error="not_found",
        message=message,
    )


def validation_error(message: str) -> APIError:
    return APIError(
        status_code=400,
        error="validation_error",
        message=message,
    )


def internal_error() -> APIError:
    return APIError(
        status_code=500,
        error="internal_error",
        message="An internal error occurred.",
    )