# ADR 0004: Use CloudFront And S3 For Frontend

The React frontend is hosted from private S3 through CloudFront.

This keeps frontend delivery separate from backend compute and supports HTTPS, caching,
and future WAF integration.

