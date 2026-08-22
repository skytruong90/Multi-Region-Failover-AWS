# Multi-Region Failover AWS

[![CI](https://github.com/skytruong90/Multi-Region-Failover-AWS/actions/workflows/ci.yml/badge.svg)](https://github.com/skytruong90/Multi-Region-Failover-AWS/actions/workflows/ci.yml)

A multi-region availability reference project that combines Terraform Route 53 failover routing with a deterministic failover state-machine simulator. It demonstrates how health signals, failover thresholds, DNS routing, recovery hysteresis, infrastructure-as-code validation, and operational reporting fit together.

> CI validates Terraform and runs the simulator only. It does not create AWS resources. `terraform apply` can create billable resources and should only be used in an authorized account.

## Architecture

```text
                         clients
                            |
                            v
                    Route 53 failover DNS
                    /                   \
             PRIMARY record        SECONDARY record
                  |                      |
          health check A          health check B
                  |                      |
                  v                      v
          region A endpoint       region B endpoint

Operational simulator:
health samples -> threshold/hysteresis -> active region -> timeline.json
```

## What it demonstrates

- Route 53 failover routing policy
- independent primary and secondary health checks
- low-TTL DNS records for recovery scenarios
- deterministic failover thresholds
- hysteresis to avoid rapid route flapping
- failure and recovery timeline generation
- Terraform validation in CI
- unit-tested operational logic

## Terraform

Configure values before planning:

```bash
terraform init
terraform plan \
  -var='hosted_zone_id=Z123EXAMPLE' \
  -var='domain_name=app.example.com' \
  -var='primary_endpoint=primary.example.net' \
  -var='secondary_endpoint=secondary.example.net'
```

The Terraform configuration creates Route 53 HTTPS health checks and failover CNAME records. The example does not provision the regional applications themselves.

## Failover simulator

Run a deterministic outage/recovery scenario:

```bash
python src/failover_sim.py --demo --output output/timeline.json
```

The demo starts on the primary region, introduces consecutive primary failures, moves traffic to secondary, then waits for multiple healthy primary samples before failing back.

Example event:

```json
{
  "step": 4,
  "event": "failover",
  "from": "primary",
  "to": "secondary",
  "reason": "primary unhealthy for 3 consecutive checks"
}
```

## Testing and validation

```bash
python -m unittest discover -s tests -v
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

## Repository layout

```text
Multi-Region-Failover-AWS/
├── main.tf
├── src/failover_sim.py
├── tests/test_failover.py
├── .github/workflows/ci.yml
└── README.md
```

## Production considerations

A real multi-region service also needs regional application/data architecture, replication semantics, RTO/RPO targets, idempotent deployment, state reconciliation, synthetic monitoring, dependency failover, observability, security controls, and rehearsed disaster-recovery runbooks. DNS failover is only one layer of that system.

## Next extensions

- weighted/canary recovery before full failback
- CloudWatch alarm inputs
- active-active routing mode
- DynamoDB Global Tables or Aurora Global Database example
- runbook automation with explicit approvals
- chaos-test scenarios and RTO/RPO reports
