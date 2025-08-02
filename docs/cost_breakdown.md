# Cost Breakdown

Estimated monthly spend for a modest production setup:

| Service | Monthly Cost (USD) | Notes |
|---------|-------------------:|-------|
| Object storage (S3) | 50 | Bronze/Silver/Gold data in S3 Standard and Glacier |
| Compute (Spark clusters) | 200 | Autoscaled to job workload |
| Streaming (Kafka/Kinesis) | 80 | Handles real-time ingestion |
| Monitoring (Grafana/CloudWatch) | 20 | Dashboards and alerts |
| Data transfer | 30 | Cross-AZ and egress traffic |
| **Total** | **380** | |

## Lifecycle Policies
- **Bronze** data retained 30 days before transition to Glacier Deep Archive.
- **Silver** data retained 90 days and moved to Infrequent Access thereafter.
- **Gold** data kept for 1 year to serve analytics workloads.
- Logs rotated every 14 days.

These policies balance performance with cost by automatically archiving or deleting data that is no longer actively queried.
