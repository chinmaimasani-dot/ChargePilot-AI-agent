# ChargePilot – Complete Address Details API

A runnable FastAPI module using NeonDB (PostgreSQL), SQLAlchemy 2.x, Alembic,
Pydantic v2 and Swagger UI.

## 1. Configure NeonDB

In Neon Console, copy the connection string for your database. Copy `.env.example`
to `.env` and replace the placeholders. Use a connection URL compatible with
psycopg 3, for example:

`postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require`

Keep `.env` private; never commit it to GitHub.

## 2. Install dependencies

Install `uv` if you do not already have it, then from this folder run:

```bash
uv sync
```

Alternatively, use `pip install -e .`.

## 3. Apply the included Alembic migration

```bash
uv run alembic upgrade head
```

This creates the `address_details` table in NeonDB. This archive includes a
baseline migration for a new, dedicated database/schema. If integrating into
your team's existing Alembic history, do NOT blindly apply this standalone
baseline. Merge the model and endpoint into the team's existing project,
import the model in its existing `alembic/env.py`, and generate a migration
against the team's current migration head. Coordinate migration history with
the team before using a shared database.

## 4. Start the API

```bash
uv run uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## 5. Create an address in Swagger

Expand `POST /api/v1/addresses/`, click **Try it out**, enter:

```json
{
  "hno": "H.No 4-5-123",
  "street_village": "Madhapur",
  "city": "Hyderabad",
  "state": "Telangana",
  "pincode": "500081",
  "lat": 17.4483,
  "long": 78.3915
}
```

Click **Execute**. A successful insert returns HTTP 201 and includes the
database-generated `id`, `created_at`, and `updated_at`.

## 6. Available endpoints

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/v1/addresses/` | Create address |
| GET | `/api/v1/addresses/` | List addresses (`skip`, `limit`) |
| GET | `/api/v1/addresses/{address_id}` | Get one address |
| PUT | `/api/v1/addresses/{address_id}` | Update address fields |
| DELETE | `/api/v1/addresses/{address_id}` | Delete address |

## Notes

- `pincode` is stored as text to preserve leading zeros.
- Latitude must be between -90 and 90; longitude between -180 and 180.
- `hno`, `lat`, and `long` are optional.
- The DB session is synchronous and uses `psycopg` 3.
- This is a complete standalone address-service scaffold, not your team's
  entire ChargePilot authentication/notification application. When merging,
  reuse your team's existing Base, engine, session dependency, router and
  Alembic history rather than duplicating them.
