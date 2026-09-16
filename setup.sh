set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"

cd "$REPO_ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() {
  echo -e "${YELLOW}==>${NC} $1";
}
ok() {
  echo -e "${GREEN}✓${NC} $1";
}
fail() {
  echo -e "${RED}✗ $1${NC}";
  exit 1;
}

# 1. Prerequisite checks
info "Checking prerequisites..."

command -v uv >/dev/null 2>&1 || fail "uv is not installed. See https://docs.astral.sh/uv/getting-started/installation/"
command -v node >/dev/null 2>&1 || fail "Node.js is not installed. See https://nodejs.org/en/download"
command -v npm >/dev/null 2>&1 || fail "npm is not installed. npm should be installed automatically with Node.js."

is_linux() {
  [ "$(uname -s)" = "Linux" ]
}

if ! docker compose version >/dev/null 2>&1; then
  if is_linux; then
    fail "Docker is not installed. Install Docker Engine: https://docs.docker.com/engine/install/"
  else
    fail "Docker is not installed. Install Docker Desktop: https://docs.docker.com/get-started/get-docker/"
  fi
fi

ok "All prerequisites found (uv, node $(node -v), docker compose)"

# 2. Env file
info "Checking .env..."
if [ ! -f "$REPO_ROOT/.env" ]; then
  if [ ! -f "$REPO_ROOT/template.env" ]; then
    fail "template.env is missing. Did you clone the repo properly?"
  fi
  cp "$REPO_ROOT/template.env" "$REPO_ROOT/.env"
  ok "Created .env from template.env"
else
  ok ".env already exists, leaving it as-is"
fi

# 3. Postgres
info "Starting Postgres..."
docker compose up -d postgres

info "Waiting for Postgres to be healthy..."
ATTEMPTS=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' sw-onboarding-db 2>/dev/null)" = "healthy" ]; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -gt 10 ]; then
    fail "Postgres did not become healthy in time. Run 'docker compose logs postgres' to debug."
  fi
  sleep 1
done
ok "Postgres is up and healthy"

# 4. Backend
info "Installing backend dependencies (uv sync)..."
uv sync
ok "Backend dependencies installed"

info "Installing pre-commit hooks..."
uv run pre-commit install
ok "Pre-commit hooks installed"

info "Running database migrations (alembic upgrade head)..."
uv run alembic upgrade head
ok "Migrations applied"

info "Seeding challenge data..."
(cd "$BACKEND_DIR" && uv run python -m scripts.seed_onboarding_data)
ok "Seed data loaded"

# 5. Frontend
info "Installing frontend dependencies (npm install)..."
(cd "$FRONTEND_DIR" && npm install)
ok "Frontend dependencies installed"

# 6. Verification
info "Verifying backend boots and responds..."
uv run fastapi dev "$BACKEND_DIR/main.py" --port 8001 >/tmp/sw-onboarding-log 2>&1 &
BACKEND_PID=$!

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

CHECK_ATTEMPTS=0
until curl -sf http://localhost:8001/api/main-commands/ >/dev/null 2>&1; do
  CHECK_ATTEMPTS=$((CHECK_ATTEMPTS + 1))
  if [ "$CHECK_ATTEMPTS" -gt 30 ]; then
    echo "---- backend log ----"
    cat /tmp/sw-onboarding-log || true
    fail "Backend did not respond at http://localhost:8001/api/main-commands/. See log above."
  fi
  sleep 1
done
ok "Backend responded successfully"

echo
ok "Setup complete."
echo "Start the backend: uv run fastapi dev backend/main.py --port 8001"
echo "Start the frontend: cd frontend && npm run dev"
