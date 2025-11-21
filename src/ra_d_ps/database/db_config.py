"""
Database Configuration for Parse Case Management
Supports both local PostgreSQL and Supabase cloud deployments
Environment-based configuration with defaults
"""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


DatabaseBackend = Literal["postgresql", "supabase"]


class PostgreSQLConfig(BaseModel):
    """PostgreSQL database configuration (local or self-hosted)"""

    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    database: str = Field(default="ra_d_ps", description="Database name")
    user: str = Field(default="ra_d_ps_user", description="Database user")
    password: str = Field(default="", description="Database password")

    # Connection pool settings
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Recycle connections after seconds")

    # SSL/TLS settings
    ssl_mode: str = Field(default="prefer", description="SSL mode: disable, allow, prefer, require")
    ssl_cert: Optional[str] = Field(default=None, description="Path to SSL certificate")
    ssl_key: Optional[str] = Field(default=None, description="Path to SSL key")
    ssl_root_cert: Optional[str] = Field(default=None, description="Path to SSL root certificate")

    # Performance settings
    echo_sql: bool = Field(default=False, description="Echo SQL statements (debug)")
    pool_pre_ping: bool = Field(default=True, description="Test connections before use")

    @classmethod
    def from_env(cls) -> "PostgreSQLConfig":
        """Load configuration from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "ra_d_ps"),
            user=os.getenv("DB_USER", "ra_d_ps_user"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            ssl_mode=os.getenv("DB_SSL_MODE", "prefer"),
            ssl_cert=os.getenv("DB_SSL_CERT"),
            ssl_key=os.getenv("DB_SSL_KEY"),
            ssl_root_cert=os.getenv("DB_SSL_ROOT_CERT"),
            echo_sql=os.getenv("DB_ECHO_SQL", "false").lower() == "true",
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
        )

    def get_connection_string(self, async_driver: bool = False) -> str:
        """
        Generate PostgreSQL connection string

        Args:
            async_driver: If True, use asyncpg driver; otherwise use psycopg2

        Returns:
            SQLAlchemy connection string
        """
        driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"

        # Build connection string
        conn_str = f"{driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        # Add SSL parameters if configured
        params = []
        if self.ssl_mode != "prefer":
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_root_cert:
            params.append(f"sslrootcert={self.ssl_root_cert}")

        if params:
            conn_str += "?" + "&".join(params)

        return conn_str

    def get_engine_kwargs(self) -> dict:
        """Get SQLAlchemy engine creation kwargs"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo_sql,
        }


class SupabaseConfig(BaseModel):
    """Supabase cloud database configuration"""

    # Supabase project details
    project_url: str = Field(..., description="Supabase project URL")
    anon_key: str = Field(..., description="Supabase anon/public API key")
    service_role_key: Optional[str] = Field(default=None, description="Supabase service role key (admin)")

    # Direct PostgreSQL connection (for SQLAlchemy)
    db_host: str = Field(..., description="Supabase PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="postgres", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(..., description="Database password")

    # Connection pool settings (cloud-optimized defaults)
    pool_size: int = Field(default=3, description="Connection pool size (smaller for cloud)")
    max_overflow: int = Field(default=5, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=1800, description="Recycle connections after 30 min")

    # SSL is required for Supabase
    ssl_mode: str = Field(default="require", description="SSL mode (always require for Supabase)")

    # Performance settings
    echo_sql: bool = Field(default=False, description="Echo SQL statements (debug)")
    pool_pre_ping: bool = Field(default=True, description="Test connections before use")

    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """Load Supabase configuration from environment variables"""
        url = os.getenv("SUPABASE_URL")
        if not url:
            raise ValueError("SUPABASE_URL must be set for Supabase backend")

        anon_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not anon_key:
            raise ValueError("SUPABASE_KEY or SUPABASE_ANON_KEY must be set")

        # Extract project ref from URL (e.g., https://abc123.supabase.co)
        project_ref = url.replace("https://", "").replace(".supabase.co", "").split(".")[0]
        db_host = f"db.{project_ref}.supabase.co"

        return cls(
            project_url=url,
            anon_key=anon_key,
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            db_host=os.getenv("SUPABASE_DB_HOST", db_host),
            db_port=int(os.getenv("SUPABASE_DB_PORT", "5432")),
            db_name=os.getenv("SUPABASE_DB_NAME", "postgres"),
            db_user=os.getenv("SUPABASE_DB_USER", "postgres"),
            db_password=os.getenv("SUPABASE_DB_PASSWORD", ""),
            pool_size=int(os.getenv("SUPABASE_POOL_SIZE", "3")),
            max_overflow=int(os.getenv("SUPABASE_MAX_OVERFLOW", "5")),
            pool_timeout=int(os.getenv("SUPABASE_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("SUPABASE_POOL_RECYCLE", "1800")),
            echo_sql=os.getenv("SUPABASE_ECHO_SQL", "false").lower() == "true",
        )

    def get_connection_string(self, async_driver: bool = False) -> str:
        """
        Generate Supabase PostgreSQL connection string

        Args:
            async_driver: If True, use asyncpg driver; otherwise use psycopg2

        Returns:
            SQLAlchemy connection string for Supabase PostgreSQL
        """
        driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"

        # Supabase connection string
        conn_str = (
            f"{driver}://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

        # Supabase requires SSL
        conn_str += "?sslmode=require"

        return conn_str

    def get_engine_kwargs(self) -> dict:
        """Get SQLAlchemy engine creation kwargs for Supabase"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo_sql,
        }


class DatabaseConfig(BaseModel):
    """Complete database configuration with backend selection"""

    # Backend selection
    backend: DatabaseBackend = Field(
        default="postgresql",
        description="Database backend: 'postgresql' (local) or 'supabase' (cloud)"
    )

    # Backend configurations
    postgresql: Optional[PostgreSQLConfig] = Field(default=None)
    supabase: Optional[SupabaseConfig] = Field(default=None)

    # Cache settings
    enable_cache: bool = Field(default=True, description="Enable in-memory caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Max cached items")

    # Retry settings
    max_retries: int = Field(default=3, description="Max connection retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")

    @classmethod
    def load(cls) -> "DatabaseConfig":
        """Load database configuration based on environment"""
        backend = os.getenv("DATABASE_BACKEND", "postgresql").lower()

        if backend not in ("postgresql", "supabase"):
            raise ValueError(f"Invalid DATABASE_BACKEND: {backend}. Must be 'postgresql' or 'supabase'")

        config_dict = {"backend": backend}

        if backend == "postgresql":
            config_dict["postgresql"] = PostgreSQLConfig.from_env()
        elif backend == "supabase":
            config_dict["supabase"] = SupabaseConfig.from_env()

        return cls(**config_dict)

    def get_active_config(self) -> PostgreSQLConfig | SupabaseConfig:
        """Get the currently active database configuration"""
        if self.backend == "postgresql":
            if not self.postgresql:
                raise ValueError("PostgreSQL backend selected but not configured")
            return self.postgresql
        elif self.backend == "supabase":
            if not self.supabase:
                raise ValueError("Supabase backend selected but not configured")
            return self.supabase
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def get_connection_string(self, async_driver: bool = False) -> str:
        """Get connection string for active backend"""
        return self.get_active_config().get_connection_string(async_driver)

    def get_engine_kwargs(self) -> dict:
        """Get engine kwargs for active backend"""
        return self.get_active_config().get_engine_kwargs()


# Global configuration instance
db_config = DatabaseConfig.load()
