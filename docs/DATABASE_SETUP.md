# PostgreSQL Database Setup for RA-D-PS Parse Case Management

This directory contains PostgreSQL database infrastructure for managing XML parse cases dynamically.

## Architecture

```
PostgreSQL Database
├── parse_cases                    # Parse case definitions
├── parse_case_profiles            # Profile configurations  
├── parse_case_detection_history   # Audit trail
└── parse_case_statistics          # Usage metrics
```

## Prerequisites

1. **PostgreSQL 12+** installed and running
2. **Python 3.9+** with dependencies from requirements.txt

## Quick Start

### 1. Install PostgreSQL (macOS)

```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Verify installation
psql --version
```

### 2. Create Database and User

```bash
# Connect as postgres superuser
psql postgres

# In psql shell:
CREATE DATABASE ra_d_ps;
CREATE USER ra_d_ps_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ra_d_ps TO ra_d_ps_user;
ALTER DATABASE ra_d_ps OWNER TO ra_d_ps_user;
\q
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env

# Set your password:
DB_PASSWORD=your_secure_password
```

### 4. Setup Database Schema

```bash
# Test connection first
python scripts/setup_database.py test

# Create tables
python scripts/setup_database.py setup

# Seed with parse cases
python scripts/seed_parse_cases.py
```

### 5. Verify Installation

```bash
# Connect to database
psql -h localhost -U ra_d_ps_user -d ra_d_ps

# In psql:
\dt                              # List tables
SELECT * FROM parse_cases;       # View parse cases
\q
```

## Database Schema

### parse_cases
Main table storing parse case definitions.

```sql
- id (UUID, PK)
- name (VARCHAR, UNIQUE)
- description (TEXT)
- detection_criteria (JSONB)     # Detection rules as JSON
- field_mappings (JSONB)         # Field mappings as JSON
- characteristic_fields (TEXT[]) # Array of field names
- requires_header (BOOLEAN)
- requires_modality (BOOLEAN)
- detection_priority (INTEGER)   # 0-100, higher = check first
- format_type (VARCHAR)          # LIDC, LIDC_v2, CXR, etc.
- is_active (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

**Example detection_criteria JSON:**
```json
{
  "min_chars": 5,
  "v2_fields": ["malignancy", "subtlety", "internalStructure"],
  "session_count": 4,
  "requires_header": true
}
```

### parse_case_profiles
Links parse cases to profile configurations.

```sql
- id (UUID, PK)
- parse_case_id (UUID, FK -> parse_cases)
- profile_name (VARCHAR)
- profile_config (JSONB)         # Full profile as JSON
- is_default (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

### parse_case_detection_history
Audit trail of parse case detections.

```sql
- id (UUID, PK)
- file_path (TEXT)
- parse_case_id (UUID, FK)
- parse_case_name (VARCHAR)
- detection_metadata (JSONB)     # Detection details
- detected_at (TIMESTAMP)
- detection_duration_ms (INTEGER)
```

### parse_case_statistics
Aggregated usage statistics.

```sql
- id (UUID, PK)
- parse_case_id (UUID, FK)
- date (DATE)
- detection_count (INTEGER)
- success_count (INTEGER)
- failure_count (INTEGER)
- avg_detection_time_ms (NUMERIC)
```

## Usage Examples

### Python API

```python
from src.ra_d_ps.database import ParseCaseRepository

# Initialize repository
repo = ParseCaseRepository()

# Create a parse case
parse_case = repo.create_parse_case(
    name="LIDC_v2_Standard",
    description="Modern LIDC-IDRI format",
    detection_criteria={
        "min_chars": 5,
        "v2_fields": ["malignancy", "subtlety", "internalStructure"],
        "requires_header": True
    },
    field_mappings=[
        {"source": "malignancy", "target": "Confidence", "type": "float"},
        {"source": "subtlety", "target": "Subtlety", "type": "float"}
    ],
    characteristic_fields=["malignancy", "subtlety", "internalStructure"],
    detection_priority=90,
    format_type="LIDC_v2"
)

# Retrieve parse case
case = repo.get_parse_case_by_name("LIDC_v2_Standard")

# Get all active parse cases (ordered by priority)
cases = repo.get_all_parse_cases(active_only=True)

# Record detection
repo.record_detection(
    file_path="/path/to/file.xml",
    parse_case_name="LIDC_v2_Standard",
    detection_metadata={"char_count": 9, "session_count": 4},
    detection_duration_ms=45
)

# Update statistics
repo.update_statistics(
    parse_case_id=parse_case.id,
    detection_count=1,
    success=True,
    detection_time_ms=45
)

repo.close()
```

### SQL Queries

```sql
-- Get all active parse cases by priority
SELECT name, detection_priority, format_type, version
FROM parse_cases
WHERE is_active = true
ORDER BY detection_priority DESC;

-- Get detection history for a file
SELECT parse_case_name, detected_at, detection_duration_ms
FROM parse_case_detection_history
WHERE file_path = '/path/to/file.xml'
ORDER BY detected_at DESC;

-- Get usage statistics for last 7 days
SELECT pc.name, SUM(pcs.detection_count) as total_detections,
       AVG(pcs.avg_detection_time_ms) as avg_time
FROM parse_case_statistics pcs
JOIN parse_cases pc ON pcs.parse_case_id = pc.id
WHERE pcs.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY pc.name
ORDER BY total_detections DESC;

-- Query parse cases with specific criteria
SELECT name, detection_criteria->>'v2_fields' as v2_fields
FROM parse_cases
WHERE detection_criteria->>'min_chars' = '5'
  AND format_type = 'LIDC_v2';
```

## Maintenance

### Backup Database

```bash
# Backup entire database
pg_dump -h localhost -U ra_d_ps_user -d ra_d_ps > backup_$(date +%Y%m%d).sql

# Backup schema only
pg_dump -h localhost -U ra_d_ps_user -d ra_d_ps --schema-only > schema.sql

# Backup data only
pg_dump -h localhost -U ra_d_ps_user -d ra_d_ps --data-only > data.sql
```

### Restore Database

```bash
# Restore from backup
psql -h localhost -U ra_d_ps_user -d ra_d_ps < backup_20251019.sql
```

### Reset Database (DESTRUCTIVE)

```bash
python scripts/setup_database.py reset
```

### View Logs

```bash
# PostgreSQL logs (macOS Homebrew)
tail -f /opt/homebrew/var/log/postgresql@15.log

# Application logs
tail -f xml_parser.log
```

## Troubleshooting

### Connection refused

```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@15

# Check port
lsof -i :5432
```

### Authentication failed

```bash
# Reset password
psql postgres -c "ALTER USER ra_d_ps_user WITH PASSWORD 'new_password';"

# Update .env file with new password
```

### Permission denied

```bash
# Grant all privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE ra_d_ps TO ra_d_ps_user;"
psql ra_d_ps -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO ra_d_ps_user;"
```

### Table already exists

```bash
# Drop and recreate
python scripts/setup_database.py reset
```

## Performance Tuning

### Connection Pooling

Configure in `.env`:
```bash
DB_POOL_SIZE=10        # Increase for high concurrency
DB_MAX_OVERFLOW=20     # Max additional connections
DB_POOL_RECYCLE=3600   # Recycle connections after 1 hour
```

### Indexes

All critical indexes are created automatically:
- `parse_cases.name` (B-tree, unique)
- `parse_cases.detection_criteria` (GIN for JSON queries)
- `parse_case_detection_history.file_path` (B-tree)
- `parse_case_detection_history.detected_at` (B-tree DESC)

### Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'ra_d_ps';

-- Table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public';

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## Migration to Production

### Using Docker

```bash
# Pull official PostgreSQL image
docker pull postgres:15

# Run container
docker run -d \
  --name ra-d-ps-postgres \
  -e POSTGRES_DB=ra_d_ps \
  -e POSTGRES_USER=ra_d_ps_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  -v ra-d-ps-data:/var/lib/postgresql/data \
  postgres:15

# Setup database
python scripts/setup_database.py setup
python scripts/seed_parse_cases.py
```

### Using Cloud (AWS RDS, Azure, GCP)

1. Create managed PostgreSQL instance
2. Update `.env` with cloud credentials:
   ```bash
   DB_HOST=your-instance.region.rds.amazonaws.com
   DB_PORT=5432
   DB_SSL_MODE=require
   ```
3. Run setup script
4. Configure security groups/firewall rules

## Support

For issues or questions:
1. Check PostgreSQL logs: `/opt/homebrew/var/log/postgresql@15.log`
2. Check application logs: `xml_parser.log`
3. Verify configuration: `python scripts/setup_database.py test`
4. Review documentation: `docs/DEVELOPER_GUIDE.md`
