# 🚀 URL Shortener Backend Service

A highly performant, production-ready backend service for URL shortening built with **FastAPI**, **PostgreSQL**, and **Redis**. This project is designed with a focus on clean architecture, security, and high-speed cache-first redirection.

---

## ✨ Features

- **User Authentication:** Secure registration and login using JWT-based authentication.
- **URL Management:** Create, list, and delete shortened URLs. Supports custom aliases and automatic expiration dates (defaults to 1 hour if not provided).
- **Cache-First Redirection:** Lightning-fast URL resolution! The API checks the Redis cache first before querying the PostgreSQL database, minimizing latency and database load.
- **Dynamic Cache Expiration:** Fully utilizes Redis TTL (Time-To-Live). Cache keys automatically expire exactly when the URL's `expires_at` timestamp is reached, ensuring expired links are never served.
- **Security:** 
  - Passwords are cryptographically hashed using `bcrypt`.
  - SSRF / Open Redirect protections during URL creation.
  - Ownership validation ensures users can only delete their own URLs.

---

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (Synchronous approach for simplicity and deterministic transaction handling)
- **Database Migrations:** Alembic
- **Caching:** Redis
- **Containerization:** Docker & Docker Compose

---

## 🏛 Architecture & Request Flow

```text
Client ──> FastAPI Server
            ├── 🔒 Auth Router (JWT Generation)
            ├── 🔗 URL Management Service
            └── 🚀 Redirect Router
                  ├── 1. Check Redis Cache for short_code
                  └── 2. Fallback to PostgreSQL (if not cached)
```

## 🐳 Running Locally (Fully Dockerized)

The entire application (FastAPI, PostgreSQL, Redis) is completely dockerized. To spin everything up at once:

1. Build and start the containers in detached mode:
   ```bash
   docker-compose up --build -d
   ```
2. Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to access the interactive Swagger API documentation.

*(Note: Alembic database migrations are automatically applied when the FastAPI container starts up!)*

### 🐞 Running Python Locally (For Debugging)

If you need to use a debugger (like VSCode or PyCharm) or just want hot-reloading for local development, you can run the FastAPI server outside of Docker while keeping the database and Redis running in containers.

1. **Stop the Docker API container** (to free up port 8000), but keep DB and Redis running:
   ```bash
   docker-compose stop api
   ```
2. **Setup your local virtual environment:**
   If this is your first time running locally, you'll need to create a virtual environment and install the dependencies.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *(If you've already done this before, just run `source venv/bin/activate`)*
3. **Run the FastAPI development server with hot-reload:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --no-access-log
   ```
*(When you are done debugging, you can restart the docker container with `docker-compose start api` or just `docker-compose up -d`)*


---

### 🗄️ Making Database Changes (Alembic)

If you modify the SQLAlchemy models (e.g., adding a new column to app/db/models.py), you need to generate a new Alembic migration script and apply it to the database. Make sure your local virtual environment is active and the database container is running.

1. *Generate the migration script:*
   ```bash
   alembic revision --autogenerate -m "describe_your_change_here"
   ```
   
2. *Apply the migration to the database:*
   ```bash
   alembic upgrade head
   ```
   
(Note: If you are running the API via Docker, the docker-compose up command automatically runs alembic upgrade head on startup, so you only need to run this manually if you are debugging outside of Docker.)

---

## 📊 Observability & Logging

- **Request Logging:** A custom FastAPI middleware intercepts every request and logs the HTTP method, path, exact response status code, and processing time in milliseconds.
- **Business Logic Auditing:** Critical events (like user registration, failed logins, cache hits vs. misses) are explicitly logged as `INFO` or `WARNING` to provide clear context without noise.
- **Global Error Handling:** Unhandled exceptions (500s) are caught by a global exception handler that logs the full Python traceback and gracefully returns a JSON error, preventing silent crashes.

---

## 🧪 Testing Suite

The project includes a robust, production-grade test suite using `pytest` and FastAPI's `TestClient`.

- **Unit Tests:** Verify core business logic like cryptographic password hashing and JWT payload structures.
- **Integration Tests:** Spin up a simulated HTTP client to test endpoints end-to-end, covering the full user journey (Registration -> Login -> URL Creation -> Redirection).
- **Database Safety:** Tests execute inside a nested PostgreSQL transaction that is automatically rolled back (`transaction.rollback()`) after every test. This guarantees that your local development database is never polluted with test data!
- **Redis Mocking:** Redis connections are fully mocked using `fakeredis` during tests to isolate cache logic.

To run the test suite locally:
```bash
# Ensure your virtual environment is active
PYTHONPATH=. pytest -v tests/
```

---

## 🚀 Future Improvements (Roadmap)

While the current architecture is robust and production-ready for moderate traffic, here are some planned improvements to scale the service further:

1. **Click Analytics:** Implement background tasks (e.g., using Celery or FastAPI BackgroundTasks) to asynchronously track geographic location, referrers, and device types for every URL click without slowing down the redirection speed.
2. **Asynchronous Database Driver:** Migrate from the synchronous `psycopg2` driver to `asyncpg` to unlock FastAPI's full asynchronous concurrency limits, allowing the server to handle thousands of simultaneous connections more efficiently.
3. **High Availability Deployment:** Migrate from a monolithic EC2 deployment to a distributed architecture using **AWS ECS (Fargate)**, managed **Amazon RDS (PostgreSQL)**, and **Amazon ElastiCache (Redis)** behind an Application Load Balancer (ALB) to handle massive horizontal scaling.
4. **Automated Cleanup:** Introduce a scheduled CRON job to routinely purge expired URLs from the PostgreSQL database to conserve storage space.
5. **Admin Dashboard:** Build a frontend (e.g., using React or Vue) to provide a UI for users to view analytics and for admins to manage user accounts.
