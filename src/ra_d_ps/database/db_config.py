"""
PostgreSQL Database Configuration for Parse Case Management
Environment-based configuration with defaults
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PostgreSQLConfig(BaseModel):
    """PostgreSQL database configuration"""
    
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


class DatabaseConfig(BaseModel):
    """Complete database configuration"""
    
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig.from_env)
    
    # Cache settings
    enable_cache: bool = Field(default=True, description="Enable in-memory caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Max cached items")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Max connection retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    
    @classmethod
    def load(cls) -> "DatabaseConfig":
        """Load database configuration"""
        return cls(postgresql=PostgreSQLConfig.from_env())


# Global configuration instance
db_config = DatabaseConfig.load()
