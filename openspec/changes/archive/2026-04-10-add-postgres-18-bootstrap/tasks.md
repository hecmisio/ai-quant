## 1. Compose Baseline

- [x] 1.1 Add a repository-root `docker-compose.yml` that defines the Anne PostgreSQL service pinned to `PostgreSQL 18.3`
- [x] 1.2 Configure the service with environment-driven database name, username, password, and host port settings
- [x] 1.3 Add persistent volume and initialization script mounts with clear repository paths

## 2. Extension Initialization

- [x] 2.1 Create a database initialization SQL script in a dedicated repository directory for first-run bootstrap
- [x] 2.2 Enable the `timescaledb` and `vector` extensions in the target database through the initialization SQL
- [x] 2.3 Ensure the initialization assets remain infrastructure-scoped and do not create Anne business tables

## 3. Verification

- [x] 3.1 Start the database with Docker Compose and confirm the container initializes successfully
- [x] 3.2 Connect to the database and verify `timescaledb` and `vector` are available after first-time setup
- [x] 3.3 Confirm the database state persists across container restarts and that initialization assets remain in version-controlled paths
