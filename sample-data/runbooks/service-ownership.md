# Service ownership map

| Service             | Team             | On-call rotation     | Tier |
|---------------------|------------------|----------------------|------|
| checkout-api        | Payments         | payments-oncall      | T1   |
| payments-service    | Payments         | payments-oncall      | T1   |
| fraud-scoring       | Trust & Safety   | trust-oncall         | T2   |
| billing-ingest      | Billing data     | billing-oncall       | T2   |
| catalog-api         | Catalog          | catalog-oncall       | T2   |
| auth-service        | Identity         | identity-oncall      | T1   |
| recommendations     | ML platform      | ml-oncall            | T3   |

Escalation: page T1 services immediately; T2/T3 page after 15 minutes if unacknowledged.
