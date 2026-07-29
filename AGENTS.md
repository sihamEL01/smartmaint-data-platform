
## `AGENTS.md`

# SmartMaint Agent Instructions

## Scope

Implement only the Jira ticket explicitly provided.

Do not modify unrelated files or implement work assigned to another ticket.

## Architecture

- Keep ingestion, transformation and loading logic separate.
- Respect the Bronze, Silver and Gold architecture.
- Preserve raw source data in Bronze.
- Keep business logic outside Airflow DAG files.

## Python

- Use type hints.
- Use clear names.
- Keep functions focused and testable.
- Use logging instead of print statements in production code.

## Data

- Define explicit schemas.
- Validate required fields.
- Detect duplicates.
- Record ingestion metadata.
- Design idempotent pipelines.
- Quarantine invalid data when required.

## Security

- Never commit secrets.
- Use environment variables.
- Never log passwords, tokens or connection strings.

## Testing

- Add tests for implemented behavior.
- Test normal, empty and invalid cases.
- Do not complete a ticket while required tests fail.

## Git

- Use one branch per Jira ticket.
- Include the Jira key in branches, commits and Pull Requests.
- Do not commit generated data, secrets or temporary files.