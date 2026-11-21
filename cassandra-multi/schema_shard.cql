CREATE KEYSPACE IF NOT EXISTS demo_fragment
WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};
USE demo_fragment;
CREATE TABLE IF NOT EXISTS evenements_by_colis (
  colis_id text, event_time timestamp, statut text, ville text, agence_id int,
  PRIMARY KEY ((colis_id), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);
CREATE TABLE IF NOT EXISTS evenements_by_agence_jour (
  agence_id int, jour date, event_time timestamp, colis_id text, statut text,
  PRIMARY KEY ((agence_id, jour), event_time, colis_id)
) WITH CLUSTERING ORDER BY (event_time DESC, colis_id ASC);
