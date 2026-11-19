"""
backend/app/core/rate_limiter.py — Shared Limiter instance for API Rate Limiting
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
