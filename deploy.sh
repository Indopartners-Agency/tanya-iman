#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source local .env if present for initial defaults
if [[ -f "$ROOT_DIR/backend/.env" ]]; then
  set -a
  source "$ROOT_DIR/backend/.env"
  set +a
fi

# Deployment defaults
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-asia-southeast2}"
ARTIFACT_REPO="${ARTIFACT_REPO:-tanya-iman}"
BACKEND_SERVICE="${BACKEND_SERVICE:-tanya-iman-backend}"
BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME:-backend}"
BACKEND_MEMORY="${BACKEND_MEMORY:-2Gi}"
BACKEND_MIN_INSTANCES="${BACKEND_MIN_INSTANCES:-1}"
BACKEND_MAX_INSTANCES="${BACKEND_MAX_INSTANCES:-20}"
INGESTION_JOB_NAME="${INGESTION_JOB_NAME:-tanya-iman-ingestion}"
INGESTION_SCHEDULE="${INGESTION_SCHEDULE:-0 2 * * 0}"
APP_SITE_ID="${APP_SITE_ID:-}"
ADMIN_SITE_ID="${ADMIN_SITE_ID:-}"
FIRESTORE_DATABASE="${FIRESTORE_DATABASE:-tanya-iman}"
BACKEND_URL="${BACKEND_URL:-}"
CORS_ORIGINS_OVERRIDE="${CORS_ORIGINS_OVERRIDE:-${CORS_ORIGINS:-}}"
# Default approved sites for FRAME_ANCESTORS (5 approved domains)
DEFAULT_FRAME_ANCESTORS="https://isadanislam.org,https://isadanalquran.com,https://isadanalfatihah.com,https://isaislamdankaumwanita.com,https://takutneraka.com"
FRAME_ANCESTORS="${FRAME_ANCESTORS:-$DEFAULT_FRAME_ANCESTORS}"

# production | staging | development
DEPLOY_ENV="${DEPLOY_ENV:-production}"

# Engine & LLM defaults
ANSWER_ENGINE="${ANSWER_ENGINE:-stub}"
PROMPT_VERSION="${PROMPT_VERSION:-0.1.0-stub}"
LLM_PROVIDER="${LLM_PROVIDER:-claude}"
LLM_MODEL="${LLM_MODEL:-claude-sonnet-4-latest}"
LLM_FALLBACK_PROVIDER="${LLM_FALLBACK_PROVIDER:-gemini}"
LLM_FALLBACK_MODEL="${LLM_FALLBACK_MODEL:-gemini-2.0-flash}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-text-multilingual-embedding-002}"
OTP_PROVIDER="${OTP_PROVIDER:-fake}"

usage() {
  cat <<'EOF'
Usage:
  bash deploy.sh [action] [options]

Actions:
  setup       One-time Google Cloud and Firebase setup (creates Secret Manager secrets, IAM, APIs)
  secrets     (Re-)create any missing Secret Manager secrets and print populate commands
  backend     Deploy backend to Cloud Run
  ingestion   Deploy ingestion Cloud Run Job and Cloud Scheduler trigger
  app         Build/deploy seeker web app to Firebase Hosting
  admin       Build/deploy admin portal to Firebase Hosting
  deploy      Deploy backend + seeker web app
  all         Deploy backend + seeker app + admin portal + firestore indexes

Options:
  --project-id <id>            Override GCP project ID (default derived from --env)
  --region <region>            Override GCP region (default: asia-southeast2)
  --database <name>            Firestore database name (default: tanya-iman)
  --app-site-id <id>           Firebase Hosting site ID for seeker app (default: tanya-iman-app)
  --admin-site-id <id>         Firebase Hosting site ID for admin portal (default: tanya-iman-admin)
  --backend-url <url>          Explicit backend URL for frontend builds
  --env <prod|staging|dev>     Deployment tier: production, staging, or development (default: production)
  --prompt-version <ver>       Override PROMPT_VERSION env var
  --llm-provider <name>        LLM provider (claude | gemini | fake)
  --llm-model <name>           LLM model identifier
  --cors-origins <origins>     Override CORS_ORIGINS (comma-separated URLs)
  --frame-ancestors <sites>    Override FRAME_ANCESTORS (comma-separated URLs)
  --min-instances <num>        Cloud Run minimum instances (default: 1)
  --memory <mem>               Cloud Run memory allocation (default: 2Gi)
  -h, --help                   Show this help message

Environment variable equivalents:
  PROJECT_ID, REGION, APP_SITE_ID, ADMIN_SITE_ID, BACKEND_URL,
  DEPLOY_ENV, PROMPT_VERSION, LLM_PROVIDER, LLM_MODEL, CORS_ORIGINS_OVERRIDE,
  FRAME_ANCESTORS, BACKEND_MEMORY, BACKEND_MIN_INSTANCES

Deployment tiers:
  production (default)  ENV=production   loads .env.production (or backend/.env)
  staging               ENV=staging      loads .env.staging
  development / dev     ENV=development  loads .env.development

Secret Manager:
  Run 'bash deploy.sh setup' once to create all Secret Manager secrets.
  Then populate each secret's value before deploying the backend:

    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-llm-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-llm-fallback-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-otp-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-otp-service-sid --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-admin-jwt-secret --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-phone-encryption-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add tanya-iman-firebase-sa --data-file=-
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_project_id() {
  if [[ -z "$PROJECT_ID" ]]; then
    if [[ "$DEPLOY_ENV" == "production" ]]; then
      PROJECT_ID="tanya-iman-prod"
    elif [[ "$DEPLOY_ENV" == "staging" ]]; then
      PROJECT_ID="tanya-iman-staging"
    elif [[ "$DEPLOY_ENV" == "development" || "$DEPLOY_ENV" == "dev" ]]; then
      PROJECT_ID="tanya-iman-dev"
    fi
  fi

  if [[ -z "$PROJECT_ID" ]]; then
    echo "PROJECT_ID is required. Set PROJECT_ID or pass --project-id:"
    echo "  bash deploy.sh setup --project-id YOUR_GCP_PROJECT_ID --region YOUR_GCP_REGION"
    exit 1
  fi
}

require_region() {
  if [[ -z "$REGION" ]]; then
    echo "REGION is required. Set REGION or pass --region:"
    echo "  bash deploy.sh setup --project-id YOUR_GCP_PROJECT_ID --region asia-southeast2"
    exit 1
  fi
}

require_deploy_config() {
  require_project_id
  require_region

  if [[ -z "$APP_SITE_ID" ]]; then
    if [[ "$DEPLOY_ENV" == "development" || "$DEPLOY_ENV" == "dev" ]]; then
      APP_SITE_ID="tanya-iman-app-dev"
    elif [[ "$DEPLOY_ENV" == "staging" ]]; then
      APP_SITE_ID="tanya-iman-app-staging"
    else
      APP_SITE_ID="tanya-iman-app"
    fi
  fi

  if [[ -z "$ADMIN_SITE_ID" ]]; then
    if [[ "$DEPLOY_ENV" == "development" || "$DEPLOY_ENV" == "dev" ]]; then
      ADMIN_SITE_ID="tanya-iman-admin-dev"
    elif [[ "$DEPLOY_ENV" == "staging" ]]; then
      ADMIN_SITE_ID="tanya-iman-admin-staging"
    else
      ADMIN_SITE_ID="tanya-iman-admin"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Secret Manager helpers
# ---------------------------------------------------------------------------

_SECRETS=(
  "tanya-iman-llm-api-key=LLM_API_KEY"
  "tanya-iman-llm-fallback-key=LLM_FALLBACK_API_KEY"
  "tanya-iman-otp-api-key=OTP_API_KEY"
  "tanya-iman-otp-service-sid=OTP_SERVICE_SID"
  "tanya-iman-admin-jwt-secret=ADMIN_JWT_SECRET"
  "tanya-iman-phone-encryption-key=PHONE_ENCRYPTION_KEY"
  "tanya-iman-firebase-sa=FIREBASE_SERVICE_ACCOUNT"
)

_ensure_secret() {
  local name="$1"
  local project="$2"
  if gcloud secrets describe "$name" --project "$project" >/dev/null 2>&1; then
    echo "  Secret '$name' already exists — skipping create."
  else
    gcloud secrets create "$name" \
      --replication-policy automatic \
      --project "$project"
    echo "  Created secret '$name'."
  fi
}

_build_set_secrets_arg() {
  local parts=()
  for entry in "${_SECRETS[@]}"; do
    local secret_name="${entry%%=*}"
    local env_var="${entry##*=}"
    parts+=("${env_var}=${secret_name}:latest")
  done
  local IFS=","
  echo "${parts[*]}"
}

_grant_secret_accessor() {
  local sa="$1"
  local project="$2"
  echo "  Granting roles/secretmanager.secretAccessor to ${sa}..."
  gcloud projects add-iam-policy-binding "$project" \
    --member="serviceAccount:${sa}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet || true
}

create_secrets() {
  echo "==> Creating Secret Manager secrets (idempotent)..."
  for entry in "${_SECRETS[@]}"; do
    local secret_name="${entry%%=*}"
    _ensure_secret "$secret_name" "$PROJECT_ID"
  done

  echo ""
  echo "All secrets exist in Secret Manager."
  echo "Populate each one before deploying the backend:"
  echo ""
  for entry in "${_SECRETS[@]}"; do
    local secret_name="${entry%%=*}"
    echo "  echo -n 'YOUR_VALUE' | gcloud secrets versions add ${secret_name} --data-file=- --project ${PROJECT_ID}"
  done
  echo ""
}

firebase_cli() {
  FIREBASE_SKIP_UPDATE_CHECK=true firebase "$@" --non-interactive
}

resolve_backend_url() {
  if [[ -n "$BACKEND_URL" ]]; then
    echo "$BACKEND_URL"
    return
  fi

  gcloud run services describe "$BACKEND_SERVICE" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format='value(status.url)'
}

setup_gcloud() {
  require_cmd gcloud
  require_cmd firebase

  echo "==> Setting active project: $PROJECT_ID"
  gcloud config set project "$PROJECT_ID"

  echo "==> Enabling required GCP APIs..."
  gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    firebase.googleapis.com \
    firebasehosting.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    cloudscheduler.googleapis.com \
    --project "$PROJECT_ID"

  echo "==> Ensuring Artifact Registry repository exists..."
  if ! gcloud artifacts repositories describe "$ARTIFACT_REPO" \
    --location "$REGION" \
    --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$ARTIFACT_REPO" \
      --repository-format docker \
      --location "$REGION" \
      --project "$PROJECT_ID"
  else
    echo "Artifact Registry repository '$ARTIFACT_REPO' already exists."
  fi

  echo "==> Configuring Docker authentication for Artifact Registry..."
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

  echo "==> Ensuring Firestore database '${FIRESTORE_DATABASE}' exists in ${REGION}..."
  if ! gcloud firestore databases describe --database="$FIRESTORE_DATABASE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud firestore databases create --database="$FIRESTORE_DATABASE" --location="$REGION" --project "$PROJECT_ID" || true
  fi

  echo "==> Linking project to Firebase (safe if already linked)..."
  firebase_cli projects:addfirebase "$PROJECT_ID" || true

  for _site_id in "$APP_SITE_ID" "$ADMIN_SITE_ID"; do
    if [[ -n "$_site_id" ]]; then
      echo "==> Ensuring Firebase Hosting site exists: $_site_id"
      firebase_cli hosting:sites:create "$_site_id" --project "$PROJECT_ID" 2>&1 \
        | grep -v "already exists" || true
    fi
  done

  # Create backend dedicated service account if it does not exist
  local sa_email="tanya-iman-backend@${PROJECT_ID}.iam.gserviceaccount.com"
  if ! gcloud iam service-accounts describe "$sa_email" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "==> Creating dedicated service account: ${sa_email}"
    gcloud iam service-accounts create "tanya-iman-backend" \
      --display-name "Tanya Iman Backend Service Account" \
      --project "$PROJECT_ID" || true
  fi

  echo "==> Granting IAM roles to service account..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${sa_email}" \
    --role="roles/datastore.user" \
    --quiet || true
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${sa_email}" \
    --role="roles/aiplatform.user" \
    --quiet || true
  _grant_secret_accessor "$sa_email" "$PROJECT_ID"

  # Also grant default compute SA for Cloud Build deployments
  local project_number
  project_number="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  local default_sa="${project_number}-compute@developer.gserviceaccount.com"
  _grant_secret_accessor "$default_sa" "$PROJECT_ID"

  # Create Secret Manager secrets
  create_secrets

  echo "==> Deploying Firestore indexes and rules for database '${FIRESTORE_DATABASE}'..."
  if [[ "$FIRESTORE_DATABASE" == "(default)" ]]; then
    firebase_cli --project "$PROJECT_ID" deploy --only firestore:rules,firestore:indexes || true
  else
    firebase_cli --project "$PROJECT_ID" deploy --only "firestore:${FIRESTORE_DATABASE}" || true
  fi

  echo ""
  echo "Setup complete."
  echo ""
  echo "IMPORTANT: Populate each secret before running 'bash deploy.sh backend'."
  echo "Run 'bash deploy.sh --help' for the list of populate commands."
}

deploy_backend() {
  require_cmd gcloud
  require_cmd firebase

  echo "==> Deploying Firestore indexes and rules for database '${FIRESTORE_DATABASE}'..."
  if [[ "$FIRESTORE_DATABASE" == "(default)" ]]; then
    firebase_cli --project "$PROJECT_ID" deploy --only firestore:rules,firestore:indexes || true
  else
    firebase_cli --project "$PROJECT_ID" deploy --only "firestore:${FIRESTORE_DATABASE}" || true
  fi

  local tag
  tag="$(date +%Y%m%d%H%M%S)"
  local image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${BACKEND_IMAGE_NAME}:${tag}"

  echo "==> Building and pushing backend image using Cloud Build (${image})..."
  gcloud builds submit --tag "$image" "$ROOT_DIR/backend" --project "$PROJECT_ID"

  # Service account email
  local sa_email="tanya-iman-backend@${PROJECT_ID}.iam.gserviceaccount.com"

  # Resolve per-environment values
  local env_name
  if [[ "$DEPLOY_ENV" == "staging" ]]; then
    env_name="staging"
  elif [[ "$DEPLOY_ENV" == "development" || "$DEPLOY_ENV" == "dev" ]]; then
    env_name="development"
  else
    env_name="production"
  fi

  # Build CORS origins
  local cors_origins
  if [[ -n "$CORS_ORIGINS_OVERRIDE" ]]; then
    cors_origins="$CORS_ORIGINS_OVERRIDE"
  else
    local _cors_parts=()
    [[ -n "$APP_SITE_ID" ]]   && _cors_parts+=("https://${APP_SITE_ID}.web.app")
    [[ -n "$ADMIN_SITE_ID" ]] && _cors_parts+=("https://${ADMIN_SITE_ID}.web.app")
    cors_origins="$(IFS=,; echo "${_cors_parts[*]}")"
  fi

  # Build remove env vars to ensure FIRESTORE_EMULATOR_HOST is completely absent
  local secret_env_vars=()
  for entry in "${_SECRETS[@]}"; do
    secret_env_vars+=("${entry##*=}")
  done
  local remove_vars
  remove_vars="FIRESTORE_EMULATOR_HOST,$(IFS=","; echo "${secret_env_vars[*]}")"

  local set_secrets_arg
  set_secrets_arg="$(_build_set_secrets_arg)"

  echo "==> Deploying backend to Cloud Run (DEPLOY_ENV=${DEPLOY_ENV})..."
  echo "    ENV=${env_name} | GCLOUD_PROJECT=${PROJECT_ID}"
  echo "    PROMPT_VERSION=${PROMPT_VERSION} | ANSWER_ENGINE=${ANSWER_ENGINE}"
  echo "    CORS_ORIGINS=${cors_origins}"
  echo "    FRAME_ANCESTORS=${FRAME_ANCESTORS}"
  echo "    MIN_INSTANCES=${BACKEND_MIN_INSTANCES} | MEMORY=${BACKEND_MEMORY}"
  echo "    Secrets mounted: ${set_secrets_arg}"

  # Deploy to Cloud Run
  gcloud run deploy "$BACKEND_SERVICE" \
    --image "$image" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --service-account "$sa_email" \
    --memory "$BACKEND_MEMORY" \
    --min-instances "$BACKEND_MIN_INSTANCES" \
    --max-instances "$BACKEND_MAX_INSTANCES" \
    --allow-unauthenticated \
    --remove-env-vars "$remove_vars" \
    --update-env-vars "^|^\
ENV=${env_name}|\
GCLOUD_PROJECT=${PROJECT_ID}|\
STORAGE_BACKEND=firestore|\
FIRESTORE_DATABASE=${FIRESTORE_DATABASE}|\
ANSWER_ENGINE=${ANSWER_ENGINE}|\
PROMPT_VERSION=${PROMPT_VERSION}|\
CORS_ORIGINS=${cors_origins}|\
FRAME_ANCESTORS=${FRAME_ANCESTORS}|\
LLM_PROVIDER=${LLM_PROVIDER}|\
LLM_MODEL=${LLM_MODEL}|\
LLM_FALLBACK_PROVIDER=${LLM_FALLBACK_PROVIDER}|\
LLM_FALLBACK_MODEL=${LLM_FALLBACK_MODEL}|\
EMBEDDING_MODEL=${EMBEDDING_MODEL}|\
OTP_PROVIDER=${OTP_PROVIDER}" \
    --set-secrets "$set_secrets_arg"

  BACKEND_URL="$(resolve_backend_url)"
  echo "Backend live at: $BACKEND_URL"

  echo "==> Checking backend health endpoint (${BACKEND_URL}/health)..."
  if curl -sf "${BACKEND_URL}/health" | grep -q '"status":"ok"'; then
    echo "  Health check OK."
  else
    echo "  Note: Health check returned non-200 or not yet ready. Verify with:"
    echo "    curl ${BACKEND_URL}/health"
  fi
}

deploy_ingestion() {
  require_cmd gcloud

  local tag
  tag="$(date +%Y%m%d%H%M%S)"
  local image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${BACKEND_IMAGE_NAME}:${tag}"
  local sa_email="tanya-iman-backend@${PROJECT_ID}.iam.gserviceaccount.com"

  echo "==> Deploying Ingestion Cloud Run Job (${INGESTION_JOB_NAME})..."
  gcloud run jobs deploy "$INGESTION_JOB_NAME" \
    --image "$image" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --service-account "$sa_email" \
    --command "python" \
    --args "-m,ingestion.run" \
    --task-timeout 3600 \
    --update-env-vars "^|^\
ENV=${DEPLOY_ENV}|\
GCLOUD_PROJECT=${PROJECT_ID}|\
STORAGE_BACKEND=firestore|\
FIRESTORE_DATABASE=${FIRESTORE_DATABASE}|\
EMBEDDING_MODEL=${EMBEDDING_MODEL}"

  echo "==> Ensuring Cloud Scheduler job (${INGESTION_JOB_NAME}-weekly) exists..."
  local scheduler_uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${INGESTION_JOB_NAME}:run"
  if gcloud scheduler jobs describe "${INGESTION_JOB_NAME}-weekly" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "${INGESTION_JOB_NAME}-weekly" \
      --location "$REGION" \
      --project "$PROJECT_ID" \
      --schedule "$INGESTION_SCHEDULE" \
      --time-zone "Asia/Jakarta" \
      --uri "$scheduler_uri" \
      --oauth-service-account-email "$sa_email"
  else
    gcloud scheduler jobs create http "${INGESTION_JOB_NAME}-weekly" \
      --location "$REGION" \
      --project "$PROJECT_ID" \
      --schedule "$INGESTION_SCHEDULE" \
      --time-zone "Asia/Jakarta" \
      --uri "$scheduler_uri" \
      --oauth-service-account-email "$sa_email"
  fi
  echo "Ingestion job scheduled: $INGESTION_SCHEDULE (Asia/Jakarta)"
}

deploy_app() {
  require_cmd npm
  require_cmd firebase

  if [[ -z "$APP_SITE_ID" ]]; then
    echo "APP_SITE_ID is required for seeker app deployment."
    echo "Provide --app-site-id <id> or set APP_SITE_ID."
    exit 1
  fi

  local backend_url firebase_config
  backend_url="$(resolve_backend_url)"
  firebase_config="$ROOT_DIR/web/app/.firebase.app.tmp.json"

  cat >"$firebase_config" <<EOF
{
  "hosting": {
    "site": "${APP_SITE_ID}",
    "public": ".output/public",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }],
    "headers": [
      {
        "source": "/embed.js",
        "headers": [{ "key": "Cache-Control", "value": "public, max-age=300" }]
      }
    ]
  }
}
EOF

  echo "==> Ensuring Firebase Hosting site exists: $APP_SITE_ID"
  firebase_cli hosting:sites:create "$APP_SITE_ID" \
    --project "$PROJECT_ID" 2>&1 \
    | grep -v "already exists" || true

  echo "==> Building seeker app (Nuxt generate)..."
  npm --prefix "$ROOT_DIR" install
  NUXT_PUBLIC_API_BASE="$backend_url" \
    NUXT_PUBLIC_DEMO_MODE="${NUXT_PUBLIC_DEMO_MODE:-0}" \
    npm --prefix "$ROOT_DIR" run build:app

  echo "==> Deploying seeker app to Firebase Hosting..."
  firebase_cli --project "$PROJECT_ID" deploy \
    --only hosting \
    --config "$firebase_config"

  rm -f "$firebase_config"
  echo "Seeker app live at: https://${APP_SITE_ID}.web.app"
}

deploy_admin() {
  require_cmd npm
  require_cmd firebase

  if [[ -z "$ADMIN_SITE_ID" ]]; then
    echo "ADMIN_SITE_ID is required for admin portal deployment."
    echo "Provide --admin-site-id <id> or set ADMIN_SITE_ID."
    exit 1
  fi

  local backend_url firebase_config
  backend_url="$(resolve_backend_url)"
  firebase_config="$ROOT_DIR/web/admin/.firebase.admin.tmp.json"

  cat >"$firebase_config" <<EOF
{
  "hosting": {
    "site": "${ADMIN_SITE_ID}",
    "public": ".output/public",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
EOF

  echo "==> Ensuring Firebase Hosting site exists: $ADMIN_SITE_ID"
  firebase_cli hosting:sites:create "$ADMIN_SITE_ID" \
    --project "$PROJECT_ID" 2>&1 \
    | grep -v "already exists" || true

  echo "==> Building admin portal (Nuxt generate)..."
  npm --prefix "$ROOT_DIR" install
  NUXT_PUBLIC_API_BASE="$backend_url" \
    NUXT_PUBLIC_DEMO_MODE="${NUXT_PUBLIC_DEMO_MODE:-0}" \
    npm --prefix "$ROOT_DIR" run build:admin

  echo "==> Deploying admin portal to Firebase Hosting..."
  firebase_cli --project "$PROJECT_ID" deploy \
    --only hosting \
    --config "$firebase_config"

  rm -f "$firebase_config"
  echo "Admin portal live at: https://${ADMIN_SITE_ID}.web.app"
}

ACTION="deploy"
if [[ $# -gt 0 && "${1:0:1}" != "-" ]]; then
  ACTION="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --database)
      FIRESTORE_DATABASE="$2"
      shift 2
      ;;
    --app-site-id)
      APP_SITE_ID="$2"
      shift 2
      ;;
    --admin-site-id)
      ADMIN_SITE_ID="$2"
      shift 2
      ;;
    --backend-url)
      BACKEND_URL="$2"
      shift 2
      ;;
    --env)
      DEPLOY_ENV="$2"
      if [[ "$DEPLOY_ENV" == "dev" ]]; then
        DEPLOY_ENV="development"
      fi
      if [[ "$DEPLOY_ENV" != "production" && "$DEPLOY_ENV" != "staging" && "$DEPLOY_ENV" != "development" ]]; then
        echo "Invalid --env value: '$DEPLOY_ENV'. Must be 'production', 'staging', or 'development' (or 'dev')."
        exit 1
      fi
      shift 2
      ;;
    --prompt-version)
      PROMPT_VERSION="$2"
      shift 2
      ;;
    --llm-provider)
      LLM_PROVIDER="$2"
      shift 2
      ;;
    --llm-model)
      LLM_MODEL="$2"
      shift 2
      ;;
    --cors-origins)
      CORS_ORIGINS_OVERRIDE="$2"
      shift 2
      ;;
    --frame-ancestors)
      FRAME_ANCESTORS="$2"
      shift 2
      ;;
    --min-instances)
      BACKEND_MIN_INSTANCES="$2"
      shift 2
      ;;
    --memory)
      BACKEND_MEMORY="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$DEPLOY_ENV" == "staging" ]]; then
  if [[ -f "$ROOT_DIR/backend/.env.staging" ]]; then
    set -a
    source "$ROOT_DIR/backend/.env.staging"
    set +a
  fi
elif [[ "$DEPLOY_ENV" == "development" ]]; then
  if [[ -f "$ROOT_DIR/backend/.env.development" ]]; then
    set -a
    source "$ROOT_DIR/backend/.env.development"
    set +a
  elif [[ -f "$ROOT_DIR/backend/.env" ]]; then
    set -a
    source "$ROOT_DIR/backend/.env"
    set +a
  fi
fi

require_deploy_config

case "$ACTION" in
  setup)
    setup_gcloud
    ;;
  secrets)
    create_secrets
    ;;
  backend)
    deploy_backend
    ;;
  ingestion)
    deploy_ingestion
    ;;
  app)
    deploy_app
    ;;
  admin)
    deploy_admin
    ;;
  deploy)
    deploy_backend
    deploy_app
    ;;
  all)
    deploy_backend
    deploy_app
    deploy_admin
    ;;
  *)
    echo "Unknown action: $ACTION"
    usage
    exit 1
    ;;
esac
