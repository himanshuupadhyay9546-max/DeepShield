# Production Deployment Guide

## AWS (Recommended for Government)
1. EKS cluster with GPU nodes (g4dn.xlarge)
2. RDS PostgreSQL Multi-AZ
3. ElastiCache Redis
4. S3 for media storage
5. CloudFront + WAF

## Azure
- AKS with NC-series VMs
- Azure Database for PostgreSQL
- Azure Cache for Redis

## GCP
- GKE with T4 GPUs
- Cloud SQL
- Memorystore

## Security Hardening
- Enable HTTPS with Let's Encrypt
- JWT rotation every 15min
- Rate limit: 100 req/min authenticated, 10/min anonymous
- Audit all detections to immutable logs
- Encrypt media at rest (AES-256)
