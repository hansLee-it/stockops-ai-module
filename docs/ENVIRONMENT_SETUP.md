# Environment Setup

## Local Files

Use `.env.example` as the template. Copy it to `.env` locally and never commit `.env`.

```bash
cp .env.example .env
```

## Public Repository Rule

Public GitHub mirrors must contain examples only. Real values belong in one of:

- Local `.env`
- GitHub Actions repository secrets
- GitHub Actions environment secrets for `dev`, `test`, or `prod`
- Runtime secret stores such as AWS Secrets Manager, when the deployment target uses AWS

## GitHub Environments

- `dev`: automatic deployment allowed from `main` or manual workflow dispatch
- `test`: manual workflow dispatch or release candidate branches
- `prod`: manual workflow dispatch, protected branch or tag, required reviewer

## Secret Naming

Use upper snake case names:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `JWT_SECRET`
- `STOCKOPS_DATASOURCE_URL`
- `STOCKOPS_DATASOURCE_USERNAME`
- `STOCKOPS_DATASOURCE_PASSWORD`
- `VITE_API_BASE_URL`
- `VITE_MQTT_WS_URL`
- `VITE_MQTT_USERNAME`
- `VITE_MQTT_PASSWORD`
- `DATABASE_URL`
- `AI_MODULE_API_KEY`

## Values That Must Not Be Committed

- Real passwords
- Access tokens
- API keys
- Private keys
- RDS endpoints
- Secret Manager ARNs
- AWS account IDs
- Terraform state
- Personal local paths
