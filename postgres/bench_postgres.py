import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor

try:
    import psycopg
    USE_PSYCOPG3 = True
except ImportError:
    import psycopg2
    USE_PSYCOPG3 = False

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "colis"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "pass"),
}
RESULTS_DIR = "results"


def get_conn():
    if USE_PSYCOPG3:
        return psycopg.connect(**DB_CONFIG, autocommit=True)
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn


def percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(round((p / 100.0) * (len(s) - 1)))
    return round(s[idx], 3)


def bench_insert(n_rows=500):
    latencies_ms = []
    t0 = time.perf_counter()
    with get_conn() as conn, conn.cursor() as cur:
        for i in range(n_rows):
            colis_id = f"BENCH_{int(time.time() * 1000)}_{i}"
            s0 = time.perf_counter()
            cur.execute(
                "INSERT INTO evenements (colis_id, event_time, statut, ville, agence_id, jour) "
                "VALUES (%s, NOW(), %s, %s, %s, CURRENT_DATE)",
                (colis_id, "EN_TRANSIT", "Douala" if i % 2 == 0 else "Yaounde", (i % 5) + 1),
            )
            latencies_ms.append((time.perf_counter() - s0) * 1000.0)
    elapsed = max(time.perf_counter() - t0, 1e-6)
    ops_per_sec = round(n_rows / elapsed, 2)
    return {
        "sgbd": "postgres",
        "mode": "insert_single",
        "rows": n_rows,
        "ops_per_sec": ops_per_sec,
        "p50_ms": percentile(latencies_ms, 50),
        "p95_ms": percentile(latencies_ms, 95),
        "p99_ms": percentile(latencies_ms, 99),
    }


def bench_read(n_iters=200):
    rows_out = []
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT colis_id FROM evenements LIMIT 200")
        colis_ids = [r[0] for r in cur.fetchall()] or ["COL00000008"]

        cur.execute("SELECT agence_id, jour FROM evenements WHERE agence_id IS NOT NULL AND jour IS NOT NULL LIMIT 200")
        agences_jours = cur.fetchall() or [(1, "2026-07-12")]

        lat_colis = []
        for i in range(n_iters):
            cid = colis_ids[i % len(colis_ids)]
            s0 = time.perf_counter()
            cur.execute("SELECT * FROM evenements WHERE colis_id = %s ORDER BY event_time", (cid,))
            cur.fetchall()
            lat_colis.append((time.perf_counter() - s0) * 1000.0)

        rows_out.append({
            "sgbd": "postgres",
            "query_type": "lecture_historique_colis",
            "iters": n_iters,
            "p50_ms": percentile(lat_colis, 50),
            "p95_ms": percentile(lat_colis, 95),
            "p99_ms": percentile(lat_colis, 99),
        })

        lat_agence = []
        for i in range(n_iters):
            ag, jr = agences_jours[i % len(agences_jours)]
            s0 = time.perf_counter()
            cur.execute(
                "SELECT * FROM evenements WHERE agence_id = %s AND jour = %s",
                (ag, jr),
            )
            cur.fetchall()
            lat_agence.append((time.perf_counter() - s0) * 1000.0)

        rows_out.append({
            "sgbd": "postgres",
            "query_type": "lecture_agence_jour",
            "iters": n_iters,
            "p50_ms": percentile(lat_agence, 50),
            "p95_ms": percentile(lat_agence, 95),
            "p99_ms": percentile(lat_agence, 99),
        })
    return rows_out


def worker_task(idx):
    s0 = time.perf_counter()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM evenements WHERE agence_id = %s",
            (1 if idx % 2 == 0 else 49,),
        )
        cur.fetchone()
    return (time.perf_counter() - s0) * 1000.0


def bench_concurrency(workers_list=(1, 4, 8), total_reqs=120):
    out = []
    for w in workers_list:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=w) as ex:
            lats = list(ex.map(worker_task, range(total_reqs)))
        elapsed = max(time.perf_counter() - t0, 1e-6)
        out.append({
            "sgbd": "postgres",
            "workers": w,
            "requests": total_reqs,
            "qps": round(total_reqs / elapsed, 2),
            "p50_ms": percentile(lats, 50),
            "p95_ms": percentile(lats, 95),
            "p99_ms": percentile(lats, 99),
        })
    return out


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ins = bench_insert(500)
    write_csv(
        os.path.join(RESULTS_DIR, "postgres_insert.csv"),
        ["sgbd", "mode", "rows", "ops_per_sec", "p50_ms", "p95_ms", "p99_ms"],
        [ins],
    )

    reads = bench_read(200)
    write_csv(
        os.path.join(RESULTS_DIR, "postgres_read.csv"),
        ["sgbd", "query_type", "iters", "p50_ms", "p95_ms", "p99_ms"],
        reads,
    )

    conc = bench_concurrency((1, 4, 8), 120)
    write_csv(
        os.path.join(RESULTS_DIR, "postgres_conc.csv"),
        ["sgbd", "workers", "requests", "qps", "p50_ms", "p95_ms", "p99_ms"],
        conc,
    )
    print("Benchmarks PostgreSQL termines dans results/")


if __name__ == "__main__":
    main()
