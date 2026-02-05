# Storage Layer

Multi-tenant database layer with PostgreSQL, SQLAlchemy, and Alembic migrations.

## Architecture

```
storage/
├── database.py       # Connection management, session factory
├── models.py         # SQLAlchemy ORM models
├── repositories.py   # Data access layer (Repository pattern)
└── __init__.py       # Public API
```

## Key Features

- **Multi-Tenancy**: Organization-level data isolation
- **Repository Pattern**: Clean separation between business logic and data access
- **Soft Deletes**: Never lose data (compliance-friendly)
- **Audit Trails**: Automatic created_at/updated_at timestamps
- **Connection Pooling**: Optimized for high-concurrency workloads
- **Type Safety**: Full type hints for better IDE support

## Models

### Organization
Multi-tenant workspace with subscription management
- Subscription tiers (FREE, BASIC, PRO, ENTERPRISE)
- Monthly usage limits and tracking
- Multiple users with roles

### User
User accounts within organizations
- Email-based authentication
- Role-based access control (OWNER, ADMIN, MEMBER, VIEWER)
- Last login tracking

### TenderDB
Procurement tender storage
- External ID for deduplication
- Processing status tracking
- Links to analysis results and bid documents

### AnalysisResult
AI agent outputs
- Filter results (relevance, confidence, categories)
- Rating results (scores, strengths, risks)
- Cost tracking per analysis

### BidDocument
Generated proposal content
- Executive summary, capabilities, approach
- Generation cost tracking
- Linked to source tender

## Usage

### Initialize Database

```python
from procurement_ai.storage import init_db

# Initialize with default URL from environment
db = init_db()

# Or provide explicit URL
db = init_db("postgresql://user:pass@localhost/mydb")
```

**Note:** Use Alembic migrations to create tables:
```bash
alembic upgrade head
```

### Using Repositories

```python
from procurement_ai.storage import (
    get_db,
    OrganizationRepository,
    TenderRepository,
)

db = get_db()

# Context manager handles commit/rollback automatically
with db.get_session() as session:
    org_repo = OrganizationRepository(session)
    
    # Create organization
    org = org_repo.create(
        name="Acme Corp",
        slug="acme",
        subscription_tier=SubscriptionTier.PRO
    )
    
    # Check usage limits
    if org_repo.can_analyze(org.id):
        # Analyze tender
        org_repo.update_usage(org.id, increment=1)
    
    # Query tenders
    tender_repo = TenderRepository(session)
    tenders = tender_repo.list_by_organization(
        org_id=org.id,
        status=TenderStatus.COMPLETE,
        limit=50
    )
```

### Multi-Tenant Isolation

All repositories enforce organization-level isolation:

```python
# User can only access tenders from their organization
tender = tender_repo.get_by_id(
    tender_id=123,
    org_id=current_user.organization_id  # Required!
)

# List only organization's tenders
tenders = tender_repo.list_by_organization(
    org_id=current_user.organization_id
)
```

## Database Migrations

Using Alembic for schema version control:

```bash
# Create initial migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show current version
alembic current
```

## Development Workflow

### 1. Start Database

```bash
# Using Docker Compose
docker-compose up -d postgres

# Or install PostgreSQL locally
brew install postgresql@15  # macOS
```

### 2. Create Migration

```bash
# After modifying models.py
alembic revision --autogenerate -m "description"

# Review generated migration in alembic/versions/

# Apply
alembic upgrade head
```

### 3. Seed Sample Data

```bash
python scripts/db_manager.py seed
```

## Repository Methods

### OrganizationRepository

```python
create(name, slug, subscription_tier) -> Organization
get_by_id(org_id) -> Organization | None
get_by_slug(slug) -> Organization | None
list_active(limit) -> List[Organization]
update_usage(org_id, increment) -> bool
can_analyze(org_id) -> bool
soft_delete(org_id) -> bool
```

### UserRepository

```python
create(organization_id, email, hashed_password, full_name, role) -> User
get_by_id(user_id) -> User | None
get_by_email(email) -> User | None
list_by_organization(org_id) -> List[User]
update_last_login(user_id) -> bool
soft_delete(user_id) -> bool
```

### TenderRepository

```python
create(organization_id, title, description, ...) -> TenderDB
get_by_id(tender_id, org_id) -> TenderDB | None
get_by_external_id(external_id, org_id) -> TenderDB | None
list_by_organization(org_id, status, limit, offset) -> List[TenderDB]
count_by_organization(org_id, status) -> int
update_status(tender_id, status, error_message, processing_time) -> bool
soft_delete(tender_id, org_id) -> bool
```

### AnalysisRepository

```python
create(tender_id, is_relevant, confidence, ...) -> AnalysisResult
get_by_tender_id(tender_id) -> AnalysisResult | None
update_rating(tender_id, overall_score, ...) -> bool
get_high_score_tenders(org_id, min_score, limit) -> List[TenderDB]
```

## Testing

Use in-memory SQLite for fast tests:

```python
from procurement_ai.storage import init_db

# Test database
db = init_db("sqlite:///:memory:")
db.create_all()

# Run tests
# ...

# Cleanup
db.drop_all()
```

## Production Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### Connection Pooling

```python
db = Database(
    database_url=os.getenv("DATABASE_URL"),
    pool_size=20,          # Persistent connections
    max_overflow=40,       # Extra connections under load
    pool_pre_ping=True,    # Verify connection health
    pool_recycle=3600,     # Recycle after 1 hour
)
```

### Read Replicas

For read-heavy workloads, separate read and write engines:

```python
# Write operations
write_engine = create_engine(PRIMARY_DB_URL)

# Read operations
read_engine = create_engine(READ_REPLICA_URL)

# Use appropriately in repositories
```

## Monitoring

Key metrics to track:
- Connection pool utilization
- Query latency (p50, p95, p99)
- Slow queries (> 100ms)
- Connection errors
- Row counts per organization

Example with Prometheus:

```python
from prometheus_client import Histogram

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

@db_query_duration.labels('list', 'tenders').time()
def list_tenders(...):
    ...
```

## Best Practices

1. **Always use repositories** - Don't query models directly
2. **Session per request** - Create new session for each operation
3. **Commit explicitly** - Or use context manager for auto-commit
4. **Paginate results** - Use limit/offset for large queries
5. **Index frequently queried columns** - Already done in models
6. **Use soft deletes** - Never hard delete (compliance, analytics)
7. **Track costs** - Store LLM costs per analysis for billing

## Schema Design Principles

- **Multi-tenancy**: Every table with user data has `organization_id`
- **Soft deletes**: `is_deleted` flag instead of DELETE
- **Audit trails**: `created_at` and `updated_at` on all tables
- **Flexibility**: JSON columns for extensible data
- **Constraints**: Unique constraints prevent duplicates
- **Indexes**: Composite indexes for common queries

## Next Steps

1. Database layer implemented
2. Testing and validation hardening
3. API and orchestration improvements
