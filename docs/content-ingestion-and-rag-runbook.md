# **Content Ingestion & RAG Runbook**

**Project:** Tanya Iman \- Corpus Operations

**Version:** 1.0

**Date:** August 2026

---

This is the operational guide for the corpus the answer engine depends on: how approved sites are crawled, chunked, embedded, and refreshed, and what to do when it goes wrong.

The corpus is **five sites in v1.0** (fixed allowlist). Scheduled crawl keeps those five current. Adding a sixth site via admin (F-42) is **post-v1.0**; the pipeline should remain ready for it. If the index is stale, thin, or contaminated with content from outside the allowlist, every guarantee in the [AI Answer Engine Specification](ai-answer-engine-specification.md) fails quietly rather than loudly.

---

## **1\. The approved sites**

`backend/config/approved_sites.yml` is the single allowlist, used by the crawler, the retriever, and the citation validator.

```yaml
sites:
  - domain: isadanislam.org
    sitemap: https://isadanislam.org/sitemap.xml
  - domain: isadanalquran.com
    sitemap: https://isadanalquran.com/sitemap.xml
  - domain: isadanalfatihah.com
    sitemap: https://isadanalfatihah.com/sitemap.xml
  - domain: isaislamdankaumwanita.com
    sitemap: https://isaislamdankaumwanita.com/sitemap.xml
  - domain: takutneraka.com
    sitemap: https://takutneraka.com/sitemap.xml
```

> **Changing this file changes the product's central promise.** Adding a domain (the expected direction) or removing one requires a PRD update (§5.3, §6.8), a crawl of the new or remaining sites, and a review of any curated answer whose citations point at a removed site. It is not a configuration tweak. The list is expected to grow.

---

## **2\. The pipeline**

```
Sitemap (or link crawl fallback)
  → Fetch          robots.txt honoured, politeness delay, identifying UA
  → Extract        main content only; strip nav, sidebar, comments, footer
  → Hash           content_hash; unchanged → skip, no writes
  → Chunk          ~400 tokens, ~80 overlap, on heading/paragraph boundaries
  → Flag           chunks containing forbidden terms → review collection
  → Embed          Vertex AI text-multilingual-embedding-002, batched
  → Upsert         articles + article_chunks
  → Retire         chunks whose parent article vanished
  → Report         articles seen / changed / written, chunks written, flags raised
```

**Idempotent by design.** Re-running over an unchanged corpus performs zero writes and costs only conditional GETs. That property is what makes a weekly schedule safe and a manual re-run harmless.

**Resumable.** An interrupted run restarts from the last completed article rather than from the beginning.

---

## **3\. Schedule and triggers**

| Trigger | Frequency | Who |
|---|---|---|
| Cloud Scheduler → Cloud Run job | Weekly, Sunday 02:00 WIB | Automatic |
| Admin portal → **Jalankan sekarang** | On demand | `super_admin`; writes an audit entry |
| CLI | Local and staging | Engineer |

```bash
# Full run
cd backend && uv run python -m ingestion.run

# One site
cd backend && uv run python -m ingestion.run --site isadanislam.org

# Dry run — reports what would change, writes nothing
cd backend && uv run python -m ingestion.run --dry-run

# Force re-embed after an embedding model change
cd backend && uv run python -m ingestion.run --force-embed
```

---

## **4\. Chunking parameters**

| Parameter | Value | Why |
|---|---|---|
| Target chunk size | ~400 tokens | Large enough to carry an argument, small enough that four fit in context without crowding |
| Overlap | ~80 tokens | Stops a definition being split from the sentence that uses it |
| Split boundaries | Heading, then paragraph, then sentence | A chunk should rarely straddle a topic change |
| Minimum chunk | 80 tokens | Shorter fragments retrieve noisily and support nothing |
| Denormalised fields | `article_id`, `site`, `url`, `title` | So a citation is produced without a second read |

Changing any of these requires a full re-chunk and re-embed, and invalidates the retrieval benchmark until it is re-run. Treat it as a migration.

---

## **5\. Embeddings**

| Setting | Value |
|---|---|
| Model | Vertex AI `text-multilingual-embedding-002` |
| Dimensionality | 768 |
| Batch size | 100 chunks |
| Stored alongside | `embedding_model` on every chunk |

**Query and corpus must use the same model.** `embedding_model` is written onto every chunk precisely so that a mismatch is detectable rather than silent. A silent mismatch does not throw an error — it just makes retrieval quietly worse, which is far harder to notice and far more damaging.

**Changing the embedding model is a full re-index.** Run `--force-embed`, verify the retrieval benchmark before switching the query-side model, and expect the similarity threshold to need re-tuning (AI Spec OI-4).

---

## **6\. Terminology flagging (AI Spec OI-1)**

Every chunk is scanned at index time for the V2 forbidden terms — `Tuhan`, `TUHAN`, `Yesus`, `Jesus`. Matches are written to a review collection with the chunk, its article, and the matched term.

This exists because Indonesian Bible translations render the divine name as "TUHAN". If an approved-site article quotes such a translation, a faithful and well-grounded answer can fail V2 through no fault of the model.

**Editorial decision required per flagged chunk:**

| Decision | Effect |
|---|---|
| `exclude` | The chunk is not retrievable. Use where the article has an equivalent passage elsewhere |
| `accept` | The chunk stays retrievable and the composer is instructed not to quote it verbatim |
| `rewrite` | The site's own wording is amended at the source, and the next crawl picks it up |

The flagged-chunk count is reported after every run and is visible in the admin portal. **This must be worked through before the pilot** — a large unresolved backlog here means unpredictable V2 failures in production.

---

## **7\. Retrieval configuration**

| Parameter | Value | Where |
|---|---|---|
| `top_k` retrieved | 8 | `backend/engine/retriever.py` |
| Passed to composer | 4 | " |
| Max chunks per article | 2 | " |
| Similarity threshold | 0.72 | `system_config`, adjustable from the admin portal |
| Minimum surviving chunks | 2 | Below this → no-grounding response (F-29) |
| Site filter | The five approved domains | Applied at query time, redundantly with the crawler |

**On the threshold.** 0.72 is an initial estimate. It must be tuned against the retrieval benchmark (PIP Task 4.5) before Phase 5, and the tuned value recorded here. Raising it makes the assistant more likely to say "we have not written about this"; lowering it makes it more likely to answer from a weak passage. The first failure mode is honest; the second is the one this product cannot afford.

---

## **8\. Monitoring**

| Signal | Healthy | Investigate when |
|---|---|---|
| Weekly run status | Success | Any failure, or two consecutive runs with zero changes across all five sites |
| Articles seen per site | Stable or growing | A drop >10% — usually a sitemap change or a redesign that broke extraction |
| Chunks written | Proportional to articles changed | Zero changes with a changed article count |
| Flagged chunks | Flat after the initial backlog is cleared | A jump — a site changed its terminology |
| `corpus_chunk_count` on `/api/health` | Matches the last run's report | Any divergence |
| No-grounding rate (K7) | <10% and falling | A rise, which usually means an ingestion failure rather than a change in what users ask |

**The most dangerous failure is a silent one.** A crawler that runs, succeeds, and extracts nothing produces a corpus that slowly ages out of relevance with no error anywhere. The "two consecutive runs with zero changes" alert exists specifically to catch that.

---

## **9\. Troubleshooting**

| Symptom | Likely cause | Action |
|---|---|---|
| Zero articles from one site | Sitemap moved or returns 404 | Check the sitemap URL; fall back to link crawling for that site |
| Articles found, chunks near-empty | Extraction is picking up navigation instead of content, usually after a theme change | Update the extraction rule for that site; add a fixture page to `tests/test_crawler.py` so the regression cannot recur |
| Embedding step fails | Vertex quota or credentials | Check the quota; the run is resumable, so re-run after fixing |
| Retrieval returns nothing for known-good questions | Embedding model mismatch | Compare `EMBEDDING_MODEL` against `embedding_model` on stored chunks; `--force-embed` if they differ |
| No-grounding rate spikes | Corpus is stale, or the threshold was raised | Check the last run; check `system_config` history in the audit log |
| Citations point at dead URLs | Article retired but chunks remain | Re-run ingestion; the retirement step handles it. If it persists, the retirement step has a bug |
| A citation from an unapproved domain appears | **Stop.** This is a V4 failure and a product-promise breach | Take the answer engine off the generated path (serve curated only), find how the chunk entered the index, and treat it as a P0 |

---

## **10\. Corpus quality review**

Automated checks confirm the pipeline ran. Only a person can confirm the corpus is any good.

**Monthly, by an editor:**

- Sample 10 chunks at random and confirm each is readable prose rather than navigation debris
- Review the Content Gaps view (Admin UX §12) and identify the top three unwritten subjects
- Review the flagged-chunk backlog and clear any new entries
- Confirm the article count per site against the site's own published count

**Quarterly:**

- Re-run the retrieval benchmark and compare recall against the last run
- Re-review the similarity threshold against the current corpus size

---

## **11\. Legal and courtesy**

- `robots.txt` is honoured. If a site's `robots.txt` disallows the crawler, that site is not crawled, and the discrepancy is raised as a product issue rather than worked around.
- A politeness delay between requests to the same host, configurable, defaulting to 2 seconds.
- An identifying User-Agent naming the project with a contact URL.
- Written confirmation that crawling and content reuse are permitted is a blocking dependency for Phase 4 (PIP B5). The sites are friendly, but "friendly" is not the same as "documented", and the person who has to answer a question about this in two years will want the document.

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [AI Answer Engine Specification](ai-answer-engine-specification.md) | How retrieval output is used, and V4/V5 grounding rules |
| [Technical Design Document](tdd.md) | §2.6, §2.9, §3.6, §3.7 |
| [Project Implementation Plan](project-implementation-plan.md) | Phase 4 |
| [Admin UX Specification](admin-ux-specification.md) | §12 Content Gaps, §14 ingestion controls |
