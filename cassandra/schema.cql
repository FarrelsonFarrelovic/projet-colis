CREATE KEYSPACE IF NOT EXISTS suivi_colis
WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 2};

USE suivi_colis;

-- Q1 : tout l'historique d'un colis
CREATE TABLE IF NOT EXISTS evenements_by_colis (
  colis_id text, event_time timestamp, statut text, ville text, agence_id int,
  PRIMARY KEY ((colis_id), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);

-- Q2 : activité d'une agence un jour donné
CREATE TABLE IF NOT EXISTS evenements_by_agence_jour (
  agence_id int, jour date, event_time timestamp, colis_id text, statut text,
  PRIMARY KEY ((agence_id, jour), event_time, colis_id)
) WITH CLUSTERING ORDER BY (event_time DESC, colis_id ASC);  