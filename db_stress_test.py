"""
Direct PostgreSQL stress test.

This does NOT go through the FastAPI backend at all -- no HTTP requests,
no routing, no Pydantic validation, no JWT, no bcrypt. It connects
straight to PostgreSQL with psycopg2 and hammers the `users` and
`transactions` tables with concurrent INSERT / SELECT / DELETE
operations, to measure the database's own performance in isolation.

Each simulated "user" (there are 1000 by default):
  1. INSERTs a row into `users`
  2. INSERTs a handful of rows into `transactions`
  3. SELECTs them back
  4. DELETEs about half of them

Run with:
    docker compose run --rm db-stress-test

Or locally, if you have psycopg2 installed and the `db` container's
port 5432 exposed to your host:
    python db_stress_test.py
"""

import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2

from app.database import Base, engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://moneynarrator:moneynarrator@localhost:5432/moneynarrator",
)

NUM_USERS = int(os.getenv("STRESS_USERS", "1000"))
TRANSACTIONS_PER_USER = int(os.getenv("STRESS_TXNS_PER_USER", "5"))
MAX_CONCURRENT_CONNECTIONS = int(os.getenv("STRESS_MAX_CONCURRENT", "50"))


def ensure_schema_exists():
    """Creates the users/transactions tables if they don't exist yet --
    reuses the same SQLAlchemy model definitions as the real app, but
    this is schema setup only. No API code runs during the actual test.
    """
    import app.models  # noqa: F401 - registers models on Base
    Base.metadata.create_all(bind=engine)


def worker(worker_id: int) -> dict:
    """Simulates one user's database activity directly over psycopg2."""
    timings = {"insert_user": 0.0, "insert_txn": 0.0, "select": 0.0, "delete": 0.0}
    error = None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        email = f"stress-{worker_id}-{uuid.uuid4().hex[:8]}@example.com"

        t0 = time.perf_counter()
        cur.execute(
            "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id",
            (email, "not-a-real-hash-this-is-a-stress-test"),
        )
        user_id = cur.fetchone()[0]
        timings["insert_user"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        txn_ids = []
        for i in range(TRANSACTIONS_PER_USER):
            cur.execute(
                """
                INSERT INTO transactions
                    (user_id, type, category, description, amount, txn_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, "discretionary", "Stress Test", f"txn {i}", 10.00, "2026-01-01"),
            )
            txn_ids.append(cur.fetchone()[0])
        timings["insert_txn"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        cur.execute("SELECT * FROM transactions WHERE user_id = %s", (user_id,))
        cur.fetchall()
        timings["select"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        for txn_id in txn_ids[: len(txn_ids) // 2]:
            cur.execute("DELETE FROM transactions WHERE id = %s", (txn_id,))
        timings["delete"] = time.perf_counter() - t0

        cur.close()
        conn.close()
    except Exception as e:
        error = str(e)

    return {"timings": timings, "error": error}


def main():
    print("Ensuring database schema exists...")
    ensure_schema_exists()

    print(f"\nDirect PostgreSQL stress test -- bypassing the FastAPI backend")
    print(f"Simulated users : {NUM_USERS}")
    print(f"Max concurrency : {MAX_CONCURRENT_CONNECTIONS} simultaneous connections")
    print(
        f"Each user does  : 1 insert (users) + {TRANSACTIONS_PER_USER} inserts "
        f"(transactions) + 1 select + {TRANSACTIONS_PER_USER // 2} deletes\n"
    )

    start = time.perf_counter()
    results = []

    # ThreadPoolExecutor: psycopg2 releases the GIL during network I/O,
    # so threads give real concurrency here without needing multiprocessing.
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CONNECTIONS) as executor:
        futures = [executor.submit(worker, i) for i in range(NUM_USERS)]
        for future in as_completed(futures):
            results.append(future.result())

    total_time = time.perf_counter() - start

    errors = [r["error"] for r in results if r["error"]]
    successful = len(results) - len(errors)

    def avg_ms(op):
        vals = [r["timings"][op] for r in results if not r["error"]]
        return (sum(vals) / len(vals) * 1000) if vals else 0.0

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total simulated users  : {NUM_USERS}")
    print(f"Successful             : {successful}")
    print(f"Errors                 : {len(errors)}")
    print(f"Total wall-clock time  : {total_time:.2f}s")
    print(f"Throughput             : {NUM_USERS / total_time:.1f} simulated users/sec")
    print()
    print("Average latency per operation (successful runs only):")
    print(f"  INSERT users        : {avg_ms('insert_user'):.2f} ms")
    print(f"  INSERT transactions : {avg_ms('insert_txn'):.2f} ms  (for {TRANSACTIONS_PER_USER} rows)")
    print(f"  SELECT              : {avg_ms('select'):.2f} ms")
    print(f"  DELETE              : {avg_ms('delete'):.2f} ms")

    if errors:
        print("\nFirst 5 errors seen:")
        for e in errors[:5]:
            print(f"  - {e}")


if __name__ == "__main__":
    main()
