# **Deployment Guide (Google Cloud & Firebase)**

**Project:** Tanya Iman

**Version:** 1.0

**Date:** August 2026

---

## **1\. What runs where**

| Component | Platform | Artefact |
|---|---|---|
| Backend API | Cloud Run (`tanya-iman-backend`) | Container from `backend/Dockerfile` |
| Ingestion job | Cloud Run Job (`tanya-iman-ingestion`) + Cloud Scheduler | Same image, different entrypoint |
| Seeker app | Firebase Hosting (site `tanya-iman-app`) | `web/app/.output/public` |
| Admin portal | Firebase Hosting (site `tanya-iman-admin`) | `web/admin/.output/public` |
| Database | Firestore (native mode, with vector index) | — |
| Secrets | Secret Manager | — |
| Android app | Google Play | AAB from `android/` |

Staging and production are **separate GCP projects**, not separate services inside one project. Separate projects give separate Firestore databases, separate quotas, separate billing lines, and no way for a mistaken flag to point staging writes at production data.

| | Staging | Production |
|---|---|---|
| GCP project | `tanya-iman-staging` | `tanya-iman-prod` |
| Backend URL | `https://api-staging.tanyaiman.id` | `https://api.tanyaiman.id` |
| Seeker app | `https://app-staging.tanyaiman.id` | `https://app.tanyaiman.id` |
| Admin portal | `https://admin-staging.tanyaiman.id` | `https://admin.tanyaiman.id` |

---

## **2\. One-time project setup**

Per environment.

```bash
gcloud config set project tanya-iman-staging

# APIs
gcloud services enable run.googleapis.com firestore.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com \
  cloudscheduler.googleapis.com firebase.googleapis.com

# Firestore
gcloud firestore databases create --location=asia-southeast2

# Indexes (composite + vector) — declared in firestore.indexes.json
firebase deploy --only firestore:indexes

# Service account for the backend
gcloud iam service-accounts create tanya-iman-backend
gcloud projects add-iam-policy-binding tanya-iman-staging \
  --member="serviceAccount:tanya-iman-backend@tanya-iman-staging.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
gcloud projects add-iam-policy-binding tanya-iman-staging \
  --member="serviceAccount:tanya-iman-backend@tanya-iman-staging.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

Firestore region is `asia-southeast2` (Jakarta). Latency to the user matters here — the answer budget is 5 seconds and a cross-region round trip per Firestore call spends it for nothing.

---

## **3\. Secrets**

Created once per environment, then referenced by name at deploy time.

```bash
echo -n "$VALUE" | gcloud secrets create tanya-iman-llm-api-key --data-file=-
```

| Secret name | Contents |
|---|---|
| `tanya-iman-llm-api-key` | LLM provider key, ZDR tier |
| `tanya-iman-llm-fallback-key` | Fallback provider key |
| `tanya-iman-otp-api-key` | WhatsApp OTP provider |
| `tanya-iman-otp-service-sid` | " |
| `tanya-iman-admin-jwt-secret` | Admin auth signing key |
| `tanya-iman-phone-encryption-key` | AES-GCM key for `phone_e164_enc` |
| `tanya-iman-firebase-sa` | Firebase service account JSON |

Rotation:

```bash
echo -n "$NEW_VALUE" | gcloud secrets versions add tanya-iman-admin-jwt-secret --data-file=-
./deploy.sh --env staging          # picks up :latest
```

`ADMIN_JWT_SECRET` and `PHONE_ENCRYPTION_KEY` are rotated independently of the provider keys.

> **Rotating `PHONE_ENCRYPTION_KEY` invalidates every stored phone number.** It requires a re-encryption migration, not a redeploy. There is no scenario where this is a routine action.

---

## **4\. Deploying the backend**

```bash
./deploy.sh --env staging     # → tanya-iman-staging
./deploy.sh                   # → tanya-iman-prod  (default is production, deliberately explicit)
```

What the script does:

```bash
gcloud run deploy tanya-iman-backend \
  --source backend/ \
  --region asia-southeast2 \
  --service-account tanya-iman-backend@${PROJECT}.iam.gserviceaccount.com \
  --set-env-vars "ENV=${ENV},GCLOUD_PROJECT=${PROJECT},PROMPT_VERSION=${PROMPT_VERSION},\
CORS_ORIGINS=${CORS_ORIGINS},FRAME_ANCESTORS=${FRAME_ANCESTORS},\
LLM_MODEL=${LLM_MODEL},EMBEDDING_MODEL=${EMBEDDING_MODEL}" \
  --set-secrets "LLM_API_KEY=tanya-iman-llm-api-key:latest,\
OTP_API_KEY=tanya-iman-otp-api-key:latest,\
ADMIN_JWT_SECRET=tanya-iman-admin-jwt-secret:latest,\
PHONE_ENCRYPTION_KEY=tanya-iman-phone-encryption-key:latest" \
  --remove-env-vars FIRESTORE_EMULATOR_HOST \
  --min-instances 1 \
  --max-instances 20
```

Three details that are not decoration:

- **`--remove-env-vars FIRESTORE_EMULATOR_HOST`.** It must be *absent*, not empty. Set to `""`, the Firestore SDK attempts a gRPC connection to an empty URI and the container crashes at startup.
- **`--min-instances 1`.** A cold start plus an LLM call blows the 5-second p50 budget. One warm instance is cheap insurance on a latency KPI.
- **`PROMPT_VERSION` is an env var, not a file read.** Rollback is a redeploy with the previous value, and because the version is stamped on every answer, the effect is measurable within hours.

**Verify immediately after every deploy:**

```bash
curl https://api-staging.tanyaiman.id/api/health
# {"status":"ok","env":"staging","prompt_version":"1.4.0","corpus_chunk_count":4182}
```

Check all four fields. A stale `prompt_version` or a `corpus_chunk_count` of zero has caught more bad deploys than any test.

---

## **5\. Deploying the frontends**

Static builds bake their configuration in. **Environment variables must be set before `npm run generate`, not before deploy.**

```bash
cd web/app
export NUXT_PUBLIC_API_BASE=https://api-staging.tanyaiman.id
export NUXT_PUBLIC_FIREBASE_API_KEY=...
export NUXT_PUBLIC_FIREBASE_PROJECT_ID=tanya-iman-staging
npm ci && npm run generate

firebase deploy --only hosting:tanya-iman-app --project tanya-iman-staging
```

```bash
cd web/admin
export NUXT_PUBLIC_API_BASE=https://api-staging.tanyaiman.id
npm ci && npm run generate
firebase deploy --only hosting:tanya-iman-admin --project tanya-iman-staging
```

> **The most common deployment failure in this architecture is a build made with the wrong `NUXT_PUBLIC_API_BASE`.** It produces an app that loads perfectly and fails every request. CI builds set these from environment secrets rather than from a developer's shell, and the deployed app exposes its API base in a `<meta>` tag so it can be checked from the browser without reading the bundle.

**After deploying a frontend, register its origin:**

- Add it to `CORS_ORIGINS` on the backend and redeploy
- Add it to Firebase Auth's authorised domains
- For the widget, add the host sites to `FRAME_ANCESTORS`

Forgetting the first is the second most common failure.

---

## **6\. Ingestion job**

```bash
gcloud run jobs deploy tanya-iman-ingestion \
  --source backend/ \
  --region asia-southeast2 \
  --command "python" --args "-m,ingestion.run" \
  --service-account tanya-iman-backend@${PROJECT}.iam.gserviceaccount.com \
  --set-env-vars "ENV=${ENV},GCLOUD_PROJECT=${PROJECT},EMBEDDING_MODEL=${EMBEDDING_MODEL}" \
  --task-timeout 3600

gcloud scheduler jobs create http tanya-iman-ingestion-weekly \
  --schedule "0 2 * * 0" --time-zone "Asia/Jakarta" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/tanya-iman-ingestion:run" \
  --oauth-service-account-email tanya-iman-backend@${PROJECT}.iam.gserviceaccount.com
```

Operational detail in [Content Ingestion & RAG Runbook](content-ingestion-and-rag-runbook.md).

---

## **7\. Firestore rules**

Clients never touch Firestore. The rules should say so unambiguously:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

The backend uses the Admin SDK and bypasses rules. This is deliberate: it means access control exists in exactly one place, in code that is tested, rather than being split between a rules file and a service layer that can disagree.

---

## **8\. Deployment order**

Order matters when a change spans layers.

**Backend-only change:** deploy backend → verify `/api/health` → smoke test.

**Frontend-only change:** build with the correct env → deploy hosting → hard-reload and verify.

**Change spanning both:** deploy the backend first if it is backwards compatible; deploy the frontend first if it is not, and gate the new backend behaviour behind a flag. Never deploy a frontend that requires a backend route that does not exist yet.

**Schema change:** add the new field, deploy the backend that writes both, backfill, deploy the code that reads the new field, then remove the old. Four deploys. Firestore is schemaless, which makes it easy to skip these steps and easy to regret it.

**Prompt change:** bump `PROMPT_VERSION`, ensure the benchmark passed in CI, deploy, then watch the validator failure rate for an hour.

---

## **9\. Rollback**

| What broke | Rollback |
|---|---|
| Backend | `gcloud run services update-traffic tanya-iman-backend --to-revisions PREVIOUS=100` |
| Frontend | `firebase hosting:rollback` — Firebase keeps prior releases |
| Prompt | Redeploy with the previous `PROMPT_VERSION` |
| Curated answer | Set its status back to `draft` in the admin portal. Instant, no deploy |
| Corpus | Re-run ingestion from the previous good commit of `approved_sites.yml` |
| Android | Halt the Play rollout; promote the previous release |

Traffic rollback on Cloud Run is seconds and does not require a rebuild. Reach for it first and diagnose afterwards.

---

## **10\. Pre-launch checklist**

Before the first production deploy:

- [ ] Production GCP project created, separate from staging
- [ ] Firestore in `asia-southeast2` with composite and vector indexes deployed
- [ ] Every secret in §3 created in the production project
- [ ] `crisis_scripts.id.yml` and emotional-deferral templates approved; numbers verified — **no placeholders** (PIP B1, B10)
- [ ] LLM provider Zero Data Retention terms confirmed in writing (PIP B3)
- [ ] `CORS_ORIGINS` lists every production frontend origin
- [ ] `FRAME_ANCESTORS` lists exactly the five approved WordPress domains
- [ ] Firebase Auth authorised domains include the production frontends
- [ ] Firestore rules deny all client access
- [ ] `--min-instances 1` set on the backend
- [ ] Full corpus crawl completed; `corpus_chunk_count` non-zero on `/api/health`
- [ ] Benchmark gates green on the production `PROMPT_VERSION`
- [ ] Monitoring alerts configured and each one triggered once to confirm it fires
- [ ] Retention purge job scheduled and verified on staging
- [ ] Privacy Policy live at the URL the app links to (PIP B9)
- [ ] Rollback rehearsed, not merely documented

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [Technical Design Document](tdd.md) | §5 environment configuration, §6 security |
| [Content Ingestion & RAG Runbook](content-ingestion-and-rag-runbook.md) | Corpus operations |
| [Android & WordPress Distribution Runbook](android-and-wordpress-distribution-runbook.md) | Store and widget release |
| [Branching and Deployment Workflow](branching-and-deployment-workflow.md) | What may be deployed from where |
