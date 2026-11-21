\connect colis
CREATE TABLE evenements (
  colis_id text NOT NULL, event_time timestamp NOT NULL,
  statut text, ville text, agence_id int, jour date,
  PRIMARY KEY (colis_id, event_time)
) PARTITION BY HASH (colis_id);
CREATE TABLE evenements_p0 PARTITION OF evenements FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE evenements_p1 PARTITION OF evenements FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE evenements_p2 PARTITION OF evenements FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE evenements_p3 PARTITION OF evenements FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_ev_agence_jour ON evenements (agence_id, jour);
