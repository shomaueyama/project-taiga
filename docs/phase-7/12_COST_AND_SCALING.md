# Cost And Scaling

Staging defaults are intentionally small and avoid NAT by default.

Production defaults:

- Two backend tasks.
- One worker task.
- Multi-AZ RDS.
- NAT gateway enabled.
- CloudFront in front of S3 frontend assets.

Capacity should be revisited after load testing with production-like data.

