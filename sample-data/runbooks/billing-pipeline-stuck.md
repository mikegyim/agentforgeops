# Runbook: Billing pipeline stuck

**Service:** billing-ingest
**Severity:** SEV-3
**Owner:** Billing data team

## Symptoms
- Kafka consumer lag > 100k on `billing.events.v2`
- `OOMKilled` events on `billing-ingest` pods
- Spark job `billing_daily_rollup` past SLA

## Likely causes
1. Memory leak in the new aggregator added in v2.14
2. Skewed partitions after a large enterprise customer onboarded
3. Schema mismatch — producer emitted an unknown field

## Remediation
1. Roll back `billing-ingest` to v2.13 if symptoms appeared after a deploy.
2. Run `kafka-consumer-groups.sh --describe --group billing-ingest` and identify lagging partitions.
3. Repartition the topic if a single partition holds >70% lag.
4. Restart the Spark job with `--executor-memory 8g` until the leak fix lands.
5. Notify #billing-ops with an ETA and impact statement.
