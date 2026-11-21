import csv, sys
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

HOSTS = sys.argv[1].split(",")                 # ex: IP1,IP2,IP3
N = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
s = Cluster(HOSTS).connect("suivi_colis")
s.default_timeout = 120
ins1 = s.prepare("INSERT INTO evenements_by_colis (colis_id,event_time,statut,ville,agence_id) VALUES (?,?,?,?,?)")
ins2 = s.prepare("INSERT INTO evenements_by_agence_jour (agence_id,jour,event_time,colis_id,statut) VALUES (?,?,?,?,?)")
a1, a2 = [], []
with open("../data/events.csv", encoding="utf-8") as f:
    for i, r in enumerate(csv.DictReader(f)):
        if i >= N: break
        ts = datetime.fromisoformat(r["event_time"])
        a1.append((r["colis_id"], ts, r["statut"], r["ville"], int(r["agence_id"])))
        a2.append((int(r["agence_id"]), ts.date(), ts, r["colis_id"], r["statut"]))
execute_concurrent_with_args(s, ins1, a1, concurrency=50)
execute_concurrent_with_args(s, ins2, a2, concurrency=50)
print(len(a1), "événements chargés")
