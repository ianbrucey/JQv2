# Test Environment Configuration

## Local (Filesystem)
- Set `CASES_BASE_PATH` to a host directory mounted into the app container
- Ensure nested runtime per-session mount via `SANDBOX_VOLUMES`

## MinIO (S3 Testing via Herd)
- Available services: Laravel Herd + MinIO
- Credentials (testing):
```
AWS_BUCKET=herd-bucket
AWS_ACCESS_KEY_ID=herd
AWS_USE_PATH_STYLE_ENDPOINT=true
AWS_SECRET_ACCESS_KEY=secretkey
AWS_DEFAULT_REGION=us-east-1
AWS_URL=https://minio.herd.test/herd-bucket
AWS_ENDPOINT=https://minio.herd.test
```
- Steps:
  1) Open MinIO dashboard; create `herd-bucket`
  2) Optionally create prefix per case
  3) Configure env vars in app container
  4) For Sync approach: verify connectivity with `aws s3 ls` or `mc ls`

## Docker Compose Notes
- Ensure network access from app container to MinIO host
- For TLS endpoints, either add CA certs to container trust store or set `AWS_CA_BUNDLE`

## Smoke Tests
- Local: create case, start conversation, create file in /workspace, verify persists
- S3 sync: start conversation, create file, stop conversation (sync back), verify in MinIO

