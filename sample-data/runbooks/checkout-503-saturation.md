# Runbook: Checkout 503 saturation

**Service:** checkout-api
**Severity:** SEV-2
**Owner:** Payments platform team
**Last reviewed:** 2026-04-12

## Symptoms
- Spike in HTTP 503 from `/v1/checkout`
- `p99_latency_ms` > 2000
- Pod count at HPA max
- Downstream `payments-service` showing elevated retries

## Likely causes
1. Synchronous calls to `fraud-scoring` taking >800ms
2. DB connection pool exhausted on `checkout-db` reader
3. Deploy of `payments-service` introducing slower contract

## Remediation
1. Check the latest deploy of `payments-service` and `fraud-scoring`. Roll back if version delta is < 30 minutes.
2. Inspect `checkout-db` connections: `SELECT count(*) FROM pg_stat_activity;`
3. Temporarily raise `HPA.maxReplicas` from 20 → 40.
4. Enable the circuit breaker for `fraud-scoring` (feature flag `cb.fraud.enabled`).
5. Page the on-call for `payments-service` if the issue persists past 15 minutes.

## Post-incident
- Open a ticket for tuning the connection pool.
- Add a synthetic that exercises checkout end-to-end every minute.
