## 1. Setup Environment Variables

The app requires secrets and configuration in a `.env` file.

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` and fill in the real secrets:

```env
# Azure Search
AI_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AI_SEARCH_INDEX="your-index"
AI_SEARCH_API_KEY="your-real-api-key"

# OpenAI
OPENAI_MODEL="gpt-4o"
OPENAI_API_URL="https://your-openai-endpoint"
OPENAI_API_KEY="your-real-api-key"

# SQL Database
SQL_DB="your_db"
SQL_HOST="your-db-host"
SQL_PORT="3306"
SQL_USER="your-db-user"
SQL_PASSWORD="your-db-password"

```

> **Note:** Do not commit your `.env` file to Git. Only `.env.example` should be in the repository.

---

## 2. Build the Docker Image

Run the following command to build the Docker image:

```bash
make build
```

This will create an image named `khub_alpha`.

---

## 3. Run the Application

To start the app in detached mode:

```bash
make run
```

This will:

- Stop and remove any existing container named `khub_alpha`
- Start a new container
- Use environment variables from `.env`
- Map port `8000` on your machine to the container

> The app will be available at: `http://localhost:8000`

---

## 4. Check Application Health

Verify the FastAPI app is running:

```bash
make health
```

Expected response:

```json
{
  "status": "ok",
  "message": "Server health check passed"
}
```

---

## 5. View Logs

To monitor logs:

```bash
make logs
```

This will show the latest 50 lines and follow new logs in real-time.

---

## 6. Access Shell in Container

To run commands inside the container:

```bash
make shell
```

---

## 7. Stop the Container

```bash
make stop
```

---

## 8. Clean Docker Images

```bash
make clean
```

> Stops the container and deletes the Docker image.

---

## 9. Tips for Clients / Deployment

1. **Secrets Management:**
   Fill all secrets in `.env` before running. For cloud deployments, use the cloud provider’s secret manager instead of committing `.env`.

2. **Ports:**
   Default port is `8000`. Ensure it’s open in firewalls/security groups.

3. **Dependencies:**
   The Dockerfile installs all Python dependencies. You don’t need to install anything on the host.

4. **Troubleshooting:**

   - If the app is not reachable, check `docker ps` to ensure the container is running.
   - Use `make logs` to debug errors.
   - Ensure `.env` variables are correct, especially endpoints and API keys.



This README ensures the client can **configure, run, and maintain the service** without touching the code, only the `.env` file and Docker commands.

---
