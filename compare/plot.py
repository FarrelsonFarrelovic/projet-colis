import glob
import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
OUT_DIR = "compare"


def load_latest_cassandra(results_dir=RESULTS_DIR):
    files = sorted(glob.glob(os.path.join(results_dir, "cassandra_test_bench_*.csv")))
    if not files:
        raise FileNotFoundError("Aucun fichier cassandra_test_bench_*.csv trouve dans results/")
    return pd.read_csv(files[-1])


def load_postgres(results_dir=RESULTS_DIR):
    ins_path = os.path.join(results_dir, "postgres_insert.csv")
    read_path = os.path.join(results_dir, "postgres_read.csv")
    conc_path = os.path.join(results_dir, "postgres_conc.csv")

    df_ins = pd.read_csv(ins_path) if os.path.exists(ins_path) else pd.DataFrame()
    df_read = pd.read_csv(read_path) if os.path.exists(read_path) else pd.DataFrame()
    df_conc = pd.read_csv(conc_path) if os.path.exists(conc_path) else pd.DataFrame()
    return df_ins, df_read, df_conc


def build_unified_tables(df_cass, df_ins, df_read, df_conc):
    throughput_rows = []
    latency_rows = []

    # Cassandra records
    for _, r in df_cass.iterrows():
        wl = str(r["workload"])
        label = f"Cassandra\n{wl}"
        if pd.notna(r.get("throughput_ops_s")):
            throughput_rows.append({
                "label": label,
                "db": "cassandra",
                "ops_per_sec": float(r["throughput_ops_s"]),
            })
        if pd.notna(r.get("p50_ms")):
            latency_rows.append({
                "label": label,
                "db": "cassandra",
                "p50_ms": float(r.get("p50_ms", 0.0) or 0.0),
                "p95_ms": float(r.get("p95_ms", 0.0) or 0.0),
                "p99_ms": float(r.get("p99_ms", 0.0) or 0.0),
            })

    # PostgreSQL insert
    for _, r in df_ins.iterrows():
        label = f"PostgreSQL\n{r['mode']}"
        throughput_rows.append({
            "label": label,
            "db": "postgres",
            "ops_per_sec": float(r["ops_per_sec"]),
        })
        latency_rows.append({
            "label": label,
            "db": "postgres",
            "p50_ms": float(r["p50_ms"]),
            "p95_ms": float(r["p95_ms"]),
            "p99_ms": float(r["p99_ms"]),
        })

    # PostgreSQL read (latencies)
    for _, r in df_read.iterrows():
        label = f"PostgreSQL\n{r['query_type']}"
        latency_rows.append({
            "label": label,
            "db": "postgres",
            "p50_ms": float(r["p50_ms"]),
            "p95_ms": float(r["p95_ms"]),
            "p99_ms": float(r["p99_ms"]),
        })

    # PostgreSQL concurrency (QPS + latencies)
    for _, r in df_conc.iterrows():
        label = f"PostgreSQL\nconc_{int(r['workers'])}w"
        throughput_rows.append({
            "label": label,
            "db": "postgres",
            "ops_per_sec": float(r["qps"]),
        })
        latency_rows.append({
            "label": label,
            "db": "postgres",
            "p50_ms": float(r["p50_ms"]),
            "p95_ms": float(r["p95_ms"]),
            "p99_ms": float(r["p99_ms"]),
        })

    return pd.DataFrame(throughput_rows), pd.DataFrame(latency_rows)


def plot_throughput(df_tp, out_path):
    if df_tp.empty:
        return
    colors = ["#2b6cb0" if db == "postgres" else "#2f855a" for db in df_tp["db"]]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bars = ax.bar(df_tp["label"], df_tp["ops_per_sec"], color=colors)
    ax.set_title("Comparaison du debit (ops/s ou QPS) - PostgreSQL vs Cassandra")
    ax.set_ylabel("Operations / requetes par seconde")
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.1f}", ha="center", va="bottom", fontsize=7)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_latencies(df_lat, out_path):
    if df_lat.empty:
        return
    x = range(len(df_lat))
    width = 0.27
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar([i - width for i in x], df_lat["p50_ms"], width=width, label="p50 (ms)")
    ax.bar(x, df_lat["p95_ms"], width=width, label="p95 (ms)")
    ax.bar([i + width for i in x], df_lat["p99_ms"], width=width, label="p99 (ms)")

    ax.set_title("Comparaison des latences (p50, p95, p99 en ms) - PostgreSQL vs Cassandra")
    ax.set_ylabel("Latence (ms)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df_lat["label"], rotation=30, ha="right", fontsize=8)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pg_concurrency(df_conc, out_path):
    if df_conc.empty:
        return
    df_c = df_conc.sort_values("workers")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    ax1.plot(df_c["workers"], df_c["qps"], marker="o", color="#2b6cb0")
    ax1.set_title("PostgreSQL - Debit selon le nombre de workers")
    ax1.set_xlabel("Workers")
    ax1.set_ylabel("QPS")
    ax1.grid(True, linestyle="--", alpha=0.4)

    ax2.plot(df_c["workers"], df_c["p50_ms"], marker="o", label="p50")
    ax2.plot(df_c["workers"], df_c["p95_ms"], marker="s", label="p95")
    ax2.plot(df_c["workers"], df_c["p99_ms"], marker="^", label="p99")
    ax2.set_title("PostgreSQL - Latences selon le nombre de workers")
    ax2.set_xlabel("Workers")
    ax2.set_ylabel("Latence (ms)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df_cass = load_latest_cassandra()
    df_ins, df_read, df_conc = load_postgres()
    df_tp, df_lat = build_unified_tables(df_cass, df_ins, df_read, df_conc)

    plot_throughput(df_tp, os.path.join(OUT_DIR, "comp_throughput.png"))
    plot_latencies(df_lat, os.path.join(OUT_DIR, "comp_latency_percentiles.png"))
    plot_pg_concurrency(df_conc, os.path.join(OUT_DIR, "comp_postgres_concurrency.png"))
    print("Graphiques generes dans compare/ avec succes.")


if __name__ == "__main__":
    main()
