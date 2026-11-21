import csv, random, sys
from datetime import datetime, timedelta

N = int(sys.argv[1]) if len(sys.argv) > 1 else 250000   # colis -> ~1,2 M d'événements
random.seed(42)
VILLES = ["Yaoundé","Douala","Bafoussam","Garoua","Bamenda","Maroua","Ngaoundéré","Bertoua","Ebolowa","Kribi"]
STATUTS = ["ENREGISTRE","RAMASSE","EN_TRANSIT","ARRIVE_HUB","EN_LIVRAISON","LIVRE"]
base = datetime(2026, 1, 1)

with open("events.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["colis_id","event_time","statut","ville","agence_id","jour"])
    for i in range(N):
        cid = f"COL{i:08d}"
        t = base + timedelta(minutes=random.randint(0, 300*24*60))
        for k in range(random.randint(4, 6)):
            w.writerow([cid, t.isoformat(sep=" "), STATUTS[k], random.choice(VILLES),
                        random.randint(1, 50), t.date().isoformat()])
            t += timedelta(hours=random.randint(1, 18))