# Disaster Recovery Plan

## Architecture Overview

- **API**: 2 instances behind nginx (least_conn)
- **Database**: TimescaleDB primary + streaming replica
- **Cache**: Redis with 3 Sentinel nodes for automatic failover
- **Message Queue**: Kafka with configurable replication factor

## RTO / RPO Targets

| Component    | RPO           | RTO           |
|-------------|---------------|---------------|
| PostgreSQL  | ~0 (sync rep) | < 5 min       |
| Redis       | < 1 min       | < 30 sec      |
| Kafka       | 0 (acks=all)  | < 2 min       |
| API         | N/A           | < 30 sec      |

## Backup Procedures

### PostgreSQL / TimescaleDB

1. **Continuous WAL archiving** (recommended):
   ```bash
   # pg_basebackup for full backup
   pg_basebackup -h db -U $POSTGRES_USER -D /backups/base -Ft -z -P

   # WAL archiving configured in postgresql.conf
   archive_mode = on
   archive_command = 'cp %p /backups/wal/%f'
   ```

2. **Scheduled pg_dump** (supplementary):
   ```bash
   # Daily logical backup
   pg_dump -h db -U $POSTGRES_USER $POSTGRES_DB | gzip > /backups/daily/$(date +%Y%m%d).sql.gz
   ```

3. **Retention**: Keep 7 daily, 4 weekly, 12 monthly backups.

### Redis

- Redis Sentinel handles automatic failover.
- RDB snapshots every 60 seconds (if >1000 keys changed).
- AOF enabled for durability.

### Kafka

- Topic replication factor >= 2 in production.
- Consumer offsets committed after successful processing.

## Failover Steps

### Database Failover

1. Sentinel or monitoring detects primary failure.
2. Promote replica: `pg_ctl promote -D /var/lib/postgresql/data`
3. Update connection strings (or use PgBouncer / HAProxy for transparent failover).
4. Rebuild old primary as new replica.

### Redis Failover

1. Redis Sentinel automatically elects new master.
2. Application uses Sentinel-aware connection (no manual intervention needed).

### API Failover

1. nginx health checks detect failed instance.
2. Traffic automatically routed to healthy instance.
3. Restart or replace failed instance.

## Recovery Testing

- Test failover quarterly.
- Restore from backup to a test environment monthly.
- Document and review results.
