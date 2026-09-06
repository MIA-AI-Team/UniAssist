# Database Setup

UniAssist uses **MySQL**, **SQLAlchemy 2.0**, and **Alembic** for database management.

## Requirements

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## 1. Create the Database

Make sure MySQL is running:

```bash
sudo systemctl start mysql
```

Create the database:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE uniassist;
EXIT;
```

## 2. Configure `.env`

Create `.env` from the example:

```bash
cp .env.example .env
```

Set the database URL:

```env
DATABASE_URL=mysql+asyncmy://USERNAME:PASSWORD@localhost:3306/uniassist
```

The `mysql+asyncmy` driver is required because the backend uses SQLAlchemy asynchronously.

## 3. Apply Migrations

The initial migration is already included in the repository. Apply all existing migrations with:

```bash
alembic upgrade head
```

Verify the database:

```bash
mysql -u root -p
```

```sql
USE uniassist;
SHOW TABLES;
```

## Making Database Changes

When modifying a SQLAlchemy model:

1. Generate a migration:

```bash
alembic revision --autogenerate -m "describe change"
```

2. Review the generated migration in:

```text
migrations/versions/
```

3. Apply it:

```bash
alembic upgrade head
```

### Useful Commands

```bash
alembic current                  # Current database revision
alembic history                  # Migration history
alembic upgrade head             # Apply all pending migrations
alembic downgrade -1             # Revert the latest migration
```

