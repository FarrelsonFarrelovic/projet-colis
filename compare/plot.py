import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
OUT_DIR = "compare"


def load_if_exists(filename):
    path = os.path.join(RESULTS_DIR, filename)
    return pd.read_csv(path) if os.path.exists(path) else None


def plot_insert():
    pg = load_if_exists("postgres_insert.csv")
    cs = load_if_exists("cassandra_insert.csv")
    frames = [f for f in [pg, cs] if f is not None and not f.empty]
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    plt.figure(figsize=(7, 4))
    plt.bar(df["sgbd"], df["ops_per_sec"])
    plt.title("Debit d'insertion (enregistrements / sec)")
    plt.ylabel("ops / sec")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "insert.png"))
    plt.close()


def plot_reads():
    pg = load_if_exists("postgres_read.csv")
    cs = load_if_exists("cassandra_read.csv")
    frames = [f for f in [pg, cs] if f is not None and not f.empty]
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    for qtype, fname in [
        ("lecture_historique_colis", "lecture_historique_colis.png"),
        ("lecture_agence_jour", "lecture_agence_jour.png"),
    ]:
        sub = df[df["query_type"] == qtype]
        if sub.empty:
            continue
        plt.figure(figsize=(7, 4))
        plt.bar(sub["sgbd"], sub["p95_ms"])
        plt.title(f"Latence p95 (ms) - {qtype}")
        plt.ylabel("ms")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, fname))
        plt.close()


def plot_concurrency():
    pg = load_if_exists("postgres_conc.csv")
    cs = load_if_exists("cassandra_conc.csv")
    frames = [f for f in [pg, cs] if f is not None and not f.empty]
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    plt.figure(figsize=(7, 4))
    for sgbd, grp in df.groupby("sgbd"):
        grp = grp.sort_values("workers")
        plt.plot(grp["workers"], grp["qps"], marker="o", label=sgbd)
    plt.title("Debit sous concurrence (QPS)")
    plt.xlabel("Workers")
    plt.ylabel("QPS")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "concurrence.png"))
    plt.close()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    plot_insert()
    plot_reads()
    plot_concurrency()
    print("Graphiques generes dans compare/")


if __name__ == "__main__":
    main()
