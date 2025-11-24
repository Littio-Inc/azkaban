# Azkaban - Authentication Service

Microservice for authentication and authorization in the Dobby ecosystem.

## 🎯 Responsibilities

- Firebase/Google OAuth authentication
- User, role, and permission management
- JWT token validation
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (MFA) with TOTP (Google Authenticator)

## 🏗️ Project Structure

```
azkaban/
├── app/
│   ├── authorizers/          # AWS API Gateway Lambda Authorizers
│   ├── common/               # Shared configuration (Firebase, secrets)
│   ├── mfa/                  # MFA/TOTP services
│   ├── middleware/           # Authentication and authorization middleware
│   ├── models/               # Database models (SQLAlchemy)
│   ├── routes/               # API routes (FastAPI)
│   └── user/                 # User management services
├── tests/                    # Unit and integration tests
├── handler.py                # Lambda entry point (Mangum)
├── serverless.yml            # Serverless Framework configuration
├── Pipfile                   # Python dependencies (Pipenv)
└── README.md
```

## 📋 Prerequisites

- Python 3.11
- Pipenv
- PostgreSQL (for local development)
- Docker and Docker Compose (optional, for local development)
- AWS CLI (for deployment)
- Node.js and npm (for Serverless Framework)

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Littio-Inc/azkaban.git
cd azkaban
```

### 2. Install dependencies

```bash
# Install Python dependencies
pipenv install --dev
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Firebase Admin SDK (Backend - Private)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com

# Database
DATABASE_URL=postgresql://azkaban:azkaban_dev@localhost:5432/azkaban_db

# Environment
ENVIRONMENT=local

# AWS Configuration (for deployment)
AWS_DEFAULT_REGION=us-east-1
VPC_SECURITY_GROUP_ID=sg-xxxxxxxxxxxxxxxxx
SUBNET_ID_ONE=subnet-xxxxxxxxxxxxxxxxx
SUBNET_ID_TWO=subnet-xxxxxxxxxxxxxxxxx
SECRET_MANAGER_AZKABAN_ARN=arn:aws:secretsmanager:region:account:secret:azkaban-staging-*
```

## 🚀 Local Development

### Option 1: With Docker Compose (Recommended)

**NOTE:** The PostgreSQL database is managed by the parent `ministry/docker-compose.yml`.

```bash
# 1. Start database from ministry (if not running)
cd ../ministry
docker-compose up -d azkaban-db

# 2. Start API from azkaban
cd azkaban
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop API (database continues running in ministry)
docker-compose down
```

### Option 2: Without Docker

```bash
# Install dependencies
pipenv install

# Run server
pipenv run uvicorn handler:app --host 0.0.0.0 --port 8001 --reload
```

**Note:** Ensure PostgreSQL is running. It can be:
- From `ministry/docker-compose.yml` (port 5433)
- Or locally on port 5432
- Update `DATABASE_URL` in `.env` accordingly

## 🧪 Testing

```bash
# Run all tests
pipenv run test

# Unit tests only
pipenv run test-unit

# Integration tests only
pipenv run test-integration

# View coverage report
pipenv run coverage-report

# Generate HTML coverage report
pipenv run coverage-html
```

## 🔍 Linting

```bash
# Run linter
pipenv run lint
```

## 🚀 Deployment

### Staging

Staging deployment runs automatically on push to `main`, or manually from GitHub Actions.

### Production

Production deployment runs manually from GitHub Actions (`workflow_dispatch`) and requires confirmation.

### Deployment Process

1. **Configure AWS Secrets Manager:**
   - Create secrets: `azkaban-staging` and `azkaban-production`
   - Include all required environment variables (see `.env.example`)

2. **Configure GitHub Secrets:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

3. **Deploy:**
   - Staging: Push to `main` branch or trigger workflow manually
   - Production: Trigger workflow manually and confirm deployment

## 📋 CI/CD

The project includes GitHub Actions workflows:

- **Checks** (`.github/workflows/checks.yml`): Runs linter, package validation, tests, and coverage on each PR
- **Staging Deployment** (`.github/workflows/staging-deployment.yml`): Deploys to staging automatically on push to `main`
- **Production Deployment** (`.github/workflows/production-deployment.yml`): Deploys to production manually with confirmation

## 🔐 Security

- Environment variables are managed via AWS Secrets Manager in production
- Sensitive credentials are never hardcoded
- `.env` files are gitignored (use `.env.example` as template)
- Firebase Admin SDK credentials are stored securely

## 📚 API Endpoints

### Authentication

- `POST /v1/auth/sync` - Sync Firebase user to database
- `GET /v1/auth/me` - Get current user information

### MFA (Multi-Factor Authentication)

- `POST /v1/auth/mfa/setup` - Setup TOTP (Google Authenticator)
- `POST /v1/auth/mfa/verify` - Verify TOTP code
- `POST /v1/auth/mfa/disable` - Disable MFA

### Users

- `GET /v1/users` - List all users (admin only)
- `GET /v1/users/me` - Get current user
- `PATCH /v1/users/{user_id}/status` - Update user status (admin only)

### Roles & Permissions

- `GET /v1/roles` - List all roles
- `GET /v1/permissions` - List all permissions

## 🛠️ Development Tools

### Scripts

- `pipenv run lint` - Run linter
- `pipenv run test` - Run all tests
- `pipenv run test-unit` - Run unit tests only
- `pipenv run test-integration` - Run integration tests only
- `pipenv run coverage-report` - Show coverage report
- `pipenv run coverage-html` - Generate HTML coverage report

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contributing guidelines here]
