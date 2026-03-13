# ADR-005: HashiCorp Vault for Secret Management

## Status

Accepted

## Date

2025-11-20

## Context

The Sit Center application requires access to multiple secrets: database credentials, Redis passwords, API keys for external integrations (i-doit, Keycloak), Kafka credentials, and ClickHouse credentials.

The original approach stored all secrets in `.env` files loaded at application startup. This had several problems:

- **No rotation**: Changing a secret required updating the `.env` file and restarting the application. There was no mechanism for automatic rotation.
- **No audit trail**: There was no record of when secrets were accessed or by whom.
- **No access control**: Anyone with filesystem access to the `.env` file could read all secrets, regardless of their role.
- **Environment parity issues**: Different environments (development, staging, production) used different `.env` files, with no centralized management or consistency checks.
- **Version control risk**: Despite `.gitignore` rules, `.env` files with production secrets have a history of being accidentally committed.

The project is deployed on Kubernetes (Helm chart in `k8s/sit-center/`), where Kubernetes Secrets provide some improvement but still lack rotation, fine-grained access control, and audit logging.

## Decision

Integrate HashiCorp Vault as the secret management backend with the following design:

1. **Three authentication methods** supported in `core/vault.py`:
   - **Token auth**: For local development and simple deployments.
   - **AppRole auth**: For production deployments outside Kubernetes (CI/CD pipelines, VM-based deployments).
   - **Kubernetes ServiceAccount auth**: For Kubernetes deployments, using the pod's service account token to authenticate with Vault.

2. **Startup injection**: At application startup, `core/vault.py` authenticates with Vault, reads secrets from the configured path, and injects them into the environment. These values override any corresponding `.env` values.

3. **Graceful fallback**: If Vault is not configured or unreachable, the application falls back to `.env` values. This ensures local development works without a Vault instance.

4. **Secret masking**: The `mask_secrets()` utility in `config.py` redacts sensitive values in log output, regardless of whether they originated from Vault or `.env`.

## Consequences

### Positive

- **Centralized secret management**: All secrets for all environments are managed in one place, with consistent policies and naming.
- **Audit trail**: Vault logs every secret access, providing visibility into which service accessed which secret and when.
- **Automatic rotation**: Vault's dynamic secrets and lease-based access enable automatic credential rotation without application restarts (for supported backends).
- **Fine-grained access control**: Vault policies restrict which services and roles can access which secrets. The API service does not need access to ML worker secrets and vice versa.
- **Multiple auth methods**: Token auth keeps local development simple. AppRole works for CI/CD. Kubernetes SA auth is native to K8s deployments. Each deployment target uses the most appropriate method.
- **Defense in depth**: Even if a container is compromised, the attacker only has access to the secrets that specific service account is authorized to read, with a time-limited lease.

### Negative

- **Infrastructure dependency**: Vault is an additional service to deploy, configure, secure, and monitor. Vault itself must be highly available in production.
- **Local development friction**: Developers can use `.env` fallback, but testing Vault-specific behavior requires a local Vault instance (e.g., `vault server -dev`).
- **Startup latency**: Vault authentication and secret retrieval add time to application startup. If Vault is slow or unreachable, startup is delayed until the timeout triggers fallback.
- **Operational complexity**: Vault unsealing, token renewal, policy management, and backup are non-trivial operational tasks that require dedicated expertise.
- **Debugging difficulty**: When secrets come from Vault rather than a local file, diagnosing "wrong credentials" issues requires checking Vault policies, paths, and lease status in addition to application configuration.
