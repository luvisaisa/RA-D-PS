"""
Supabase client configuration and integration.

Provides both REST API client and PostgreSQL connection for Supabase.
Automatically initialized when DATABASE_BACKEND=supabase.
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# Supabase REST API Client (optional, only if supabase-py is installed)
_supabase_client: Optional[any] = None


def get_supabase_client():
    """
    Get Supabase REST API client (lazy initialization).

    The Supabase client provides access to:
    - Database tables via REST API
    - Authentication
    - Storage
    - Realtime subscriptions
    - Edge functions

    For direct SQL queries, use SQLAlchemy with get_supabase_engine() instead.

    Returns:
        Supabase client instance

    Raises:
        ImportError: If supabase-py is not installed
        RuntimeError: If SUPABASE_URL or SUPABASE_KEY not set
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    try:
        from supabase import create_client, Client
    except ImportError:
        raise ImportError(
            "supabase-py is not installed. Install with: pip install supabase"
        )

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment. "
            "Check your .env file or environment variables."
        )

    _supabase_client = create_client(url, key)
    return _supabase_client


def get_supabase_service_client():
    """
    Get Supabase service role client with admin privileges.

    WARNING: Service role key bypasses Row Level Security (RLS).
    Only use for administrative tasks and backend operations.

    Returns:
        Supabase client with service role privileges

    Raises:
        ImportError: If supabase-py is not installed
        RuntimeError: If credentials not set
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        raise ImportError(
            "supabase-py is not installed. Install with: pip install supabase"
        )

    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for service client"
        )

    return create_client(url, service_key)


def is_supabase_available() -> bool:
    """
    Check if Supabase is configured and available.

    Returns:
        True if SUPABASE_URL and SUPABASE_KEY are set
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    return bool(url and key)


# Convenience export (lazy-loaded)
try:
    supabase = get_supabase_client()
except (ImportError, RuntimeError):
    # Supabase not configured or supabase-py not installed
    # This is okay - user might be using local PostgreSQL
    supabase = None


__all__ = [
    "get_supabase_client",
    "get_supabase_service_client",
    "is_supabase_available",
    "supabase",
]
