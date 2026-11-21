#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 -U postgres -c "CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'repl';"
echo "host replication replicator all scram-sha-256" >> "$PGDATA/pg_hba.conf"
