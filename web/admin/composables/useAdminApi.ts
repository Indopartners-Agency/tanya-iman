import { useSessionStore } from '~/stores/session'
import * as fixtures from '~/demo/fixtures'

export function useAdminApi() {
  const config = useRuntimeConfig()
  const session = useSessionStore()
  const router = useRouter()
  const demo = useDemoMode()

  const liveGapCount = useState<number>('admin_gap_count', () => (demo ? fixtures.gapCount : 0))
  const liveReviewCount = useState<number>('admin_review_count', () =>
    demo ? fixtures.reviewCount : 0,
  )

  const baseUrl = (config.public.apiBase || 'http://localhost:8000').replace(/\/$/, '')

  async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {})
    if (session.accessToken) {
      headers.set('Authorization', `Bearer ${session.accessToken}`)
    }
    if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
      headers.set('Content-Type', 'application/json')
    }

    const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

    let res = await fetch(url, { ...options, headers })

    if (res.status === 401) {
      if (session.refreshToken) {
        const newToken = await session.refresh()
        if (newToken) {
          headers.set('Authorization', `Bearer ${newToken}`)
          res = await fetch(url, { ...options, headers })
        }
      }
      if (res.status === 401) {
        session.signOut()
        if (!demo) {
          await router.push('/masuk')
        }
        throw new Error('Sesi berakhir. Silakan masuk kembali.')
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      const detail =
        typeof err?.detail === 'string' ? err.detail : `Permintaan gagal (${res.status})`
      throw new Error(detail)
    }

    if (res.status === 204) {
      return undefined as unknown as T
    }

    return res.json() as Promise<T>
  }

  // --- Dashboard ---
  async function getDashboard() {
    if (demo) {
      liveGapCount.value = fixtures.gaps.length
      liveReviewCount.value = fixtures.reviewCount
      return {
        total_questions: fixtures.dashboard.volumeThisWeek,
        volume_change_pct: fixtures.dashboard.volumeChangePct,
        total_likes: 42,
        active_topics: fixtures.topics.length,
        curated_coverage: 71.4,
        recent_refusals: 1,
        recent_crises: 0,
        ungrounded_gaps: fixtures.gaps.length,
        review_items: fixtures.reviewCount,
        validator_pass_pct: fixtures.dashboard.validatorPassPct,
        answer_rate_pct: fixtures.dashboard.answerRatePct,
        like_rate_pct: fixtures.dashboard.likeRatePct,
        top_topics: fixtures.topics.slice(0, 5),
        largest_gap: fixtures.gaps[0],
      }
    }

    const data = await request<any>('/api/admin/dashboard')
    liveGapCount.value = data.ungrounded_gaps ?? 0
    liveReviewCount.value = data.review_items ?? 0
    return {
      total_questions: data.total_questions,
      volume_change_pct: 15,
      total_likes: data.total_likes,
      active_topics: data.active_topics,
      curated_coverage: data.curated_coverage,
      recent_refusals: data.recent_refusals,
      recent_crises: data.recent_crises,
      ungrounded_gaps: data.ungrounded_gaps,
      review_items: data.review_items,
      validator_pass_pct: data.validator_pass_pct ?? 100,
      answer_rate_pct: data.answer_rate_pct ?? 100,
      like_rate_pct:
        data.total_questions > 0 ? Math.round((data.total_likes / data.total_questions) * 100) : 0,
      top_topics: (data.top_topics || []).map((t: any) => ({
        slug: t.slug,
        label: t.label,
        questions: t.questions,
        likes: t.likes,
        curated: t.curated,
        curatedBy: t.curated_by,
        curatedAt: t.curated_at,
        curatedAnswer: t.curated_answer,
        curatedCitations: t.curated_citations,
        refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : t.refusal_rate || 0,
      })),
      largest_gap: null,
    }
  }

  // --- Topics ---
  async function getTopics() {
    if (demo) return fixtures.topics

    const data = await request<any[]>('/api/admin/topics')
    return data.map((t: any) => ({
      slug: t.slug,
      label: t.label,
      questions: t.questions,
      likes: t.likes,
      curated: t.curated,
      curatedBy: t.curated_by,
      curatedAt: t.curated_at,
      curatedAnswer: t.curated_answer,
      curatedCitations: t.curated_citations || [],
      refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : t.refusal_rate || 0,
    }))
  }

  async function getTopic(slug: string) {
    if (demo) return fixtures.topics.find((t) => t.slug === slug) || null

    const t = await request<any>(`/api/admin/topics/${slug}`)
    return {
      slug: t.slug,
      label: t.label,
      questions: t.questions,
      likes: t.likes,
      curated: t.curated,
      curatedBy: t.curated_by,
      curatedAt: t.curated_at,
      curatedAnswer: t.curated_answer,
      curatedCitations: t.curated_citations || [],
      refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : t.refusal_rate || 0,
    }
  }

  async function updateTopicAnswer(
    slug: string,
    answerText: string,
    status: 'draft' | 'published',
    citations: any[] = [],
  ) {
    if (demo) {
      const existing = fixtures.topics.find((t) => t.slug === slug)
      if (existing) {
        existing.curated = status
      }
      return existing
    }

    return request<any>(`/api/admin/topics/${slug}/answer`, {
      method: 'PUT',
      body: JSON.stringify({
        answer_text: answerText,
        status,
        citations,
      }),
    })
  }

  // --- Corpus Articles ---
  async function getArticles(query?: string, site?: string) {
    if (demo) {
      return fixtures.articles.map((a) => ({
        id: a.id,
        title: a.title,
        url: `https://${a.site}/${a.id}`,
        site: a.site,
      }))
    }

    const params = new URLSearchParams()
    if (query) params.set('q', query)
    if (site) params.set('site', site)
    params.set('limit', '100')
    const data = await request<any[]>(`/api/admin/articles?${params.toString()}`)
    return data.map((a: any) => ({
      id: a.id,
      title: a.title,
      url: a.url,
      site: a.site,
    }))
  }

  // --- Questions ---
  async function getQuestions(filters?: {
    topic?: string
    result?: string
    search?: string
    channel?: string
    validator?: string
    dateFrom?: string
    dateTo?: string
  }) {
    if (demo) return fixtures.questions

    const params = new URLSearchParams()
    if (filters?.search) params.set('q', filters.search)
    if (filters?.topic) params.set('topic', filters.topic)
    if (filters?.result) params.set('source', filters.result)
    if (filters?.channel) params.set('channel', filters.channel)
    if (filters?.validator) params.set('validator', filters.validator)
    if (filters?.dateFrom) params.set('date_from', filters.dateFrom)
    if (filters?.dateTo) params.set('date_to', filters.dateTo)
    params.set('limit', '200')

    const data = await request<any[]>(`/api/admin/questions?${params.toString()}`)
    return data.map((q: any) => ({
      id: q.id,
      askedAt: q.asked_at,
      question: q.question,
      topicSlug: q.topic_slug,
      topicLabel: q.topic_label,
      result: q.result,
      likes: q.likes,
      channel: q.channel || 'web',
      flags: q.flags || [],
    }))
  }

  async function exportQuestionsCsv(filters?: {
    topic?: string
    result?: string
    search?: string
    channel?: string
    validator?: string
    dateFrom?: string
    dateTo?: string
  }): Promise<string> {
    if (demo) return ''
    const params = new URLSearchParams()
    if (filters?.search) params.set('q', filters.search)
    if (filters?.topic) params.set('topic', filters.topic)
    if (filters?.result) params.set('source', filters.result)
    if (filters?.channel) params.set('channel', filters.channel)
    if (filters?.validator) params.set('validator', filters.validator)
    if (filters?.dateFrom) params.set('date_from', filters.dateFrom)
    if (filters?.dateTo) params.set('date_to', filters.dateTo)

    const headers = new Headers()
    if (session.accessToken) {
      headers.set('Authorization', `Bearer ${session.accessToken}`)
    }
    const url = `${baseUrl}/api/admin/questions/export?${params.toString()}`
    let res = await fetch(url, { headers })
    if (res.status === 401) {
      if (session.refreshToken) {
        const newToken = await session.refresh()
        if (newToken) {
          headers.set('Authorization', `Bearer ${newToken}`)
          res = await fetch(url, { headers })
        }
      }
      if (res.status === 401) {
        session.signOut()
        if (!demo) {
          await router.push('/masuk')
        }
        throw new Error('Sesi berakhir. Silakan masuk kembali.')
      }
    }
    if (!res.ok) {
      throw new Error(`Ekspor gagal (${res.status})`)
    }
    return res.text()
  }

  async function getQuestionDetail(id: string) {
    if (demo) {
      const q = fixtures.questions.find((q) => q.id === id)
      if (!q) return null
      return {
        ...q,
        answer: (q as any).answer || 'Jawaban contoh dari sistem.',
        retrievedChunks: fixtures.retrievedChunks,
        validators: fixtures.validators,
        validatorFailures: [],
        repair: null,
        flaggedForReview: false,
      }
    }

    const q = await request<any>(`/api/admin/questions/${id}`)
    return {
      id: q.id,
      askedAt: q.asked_at,
      question: q.question,
      answer: q.answer,
      topicSlug: q.topic_slug,
      topicLabel: q.topic_label,
      result: q.result,
      likes: q.likes,
      channel: q.channel || 'web',
      citations: q.citations || [],
      retrievedChunkIds: q.retrieved_chunk_ids || [],
      retrievedChunks: (q.retrieved_chunks || []).map((c: any) => ({
        id: c.id,
        articleTitle: c.article_title || c.title || 'Artikel',
        site: c.site,
        url: c.url,
        score: c.score ?? 0,
        cited: Boolean(c.cited),
        text: c.text,
      })),
      validators: (q.validators || []).map((v: any) => ({
        code: v.code,
        label: v.label,
        pass: v.pass ?? v.pass_ ?? true,
        measured: v.measured || '',
        failureCodes: v.failure_codes || [],
      })),
      validatorFailures: q.validator_failures || [],
      repair: q.repair
        ? {
            attempted: Boolean(q.repair.attempted),
            succeeded: Boolean(q.repair.succeeded),
            initialFailures: q.repair.initial_failures || [],
            finalFailures: q.repair.final_failures || [],
            summary: q.repair.summary || '',
          }
        : null,
      flaggedForReview: Boolean(q.flagged_for_review),
      classificationScore: q.classification_score ?? 0.94,
      model: q.model,
      promptVersion: q.prompt_version,
      latencyMs: q.latency_ms,
    }
  }

  async function flagQuestion(id: string) {
    if (demo) {
      return { status: 'ok', question_id: id, flagged: true }
    }
    return request<any>(`/api/admin/questions/${id}/flag`, {
      method: 'POST',
    })
  }

  async function deleteQuestion(id: string) {
    if (demo) {
      return { status: 'ok', deleted_id: id, audit_id: `aud_demo_${id}` }
    }
    return request<any>(`/api/admin/questions/${id}`, {
      method: 'DELETE',
    })
  }

  // --- Gaps ---
  async function getGaps() {
    if (demo) {
      liveGapCount.value = fixtures.gaps.length
      return fixtures.gaps
    }

    const data = await request<any[]>('/api/admin/gaps')
    liveGapCount.value = data.length
    return data
  }

  async function resolveGap(gapId: string) {
    if (demo) {
      liveGapCount.value = Math.max(0, liveGapCount.value - 1)
      return { status: 'ok', resolved_id: gapId }
    }
    const res = await request<any>(`/api/admin/gaps/${encodeURIComponent(gapId)}/resolve`, {
      method: 'POST',
    })
    liveGapCount.value = Math.max(0, liveGapCount.value - 1)
    return res
  }

  // --- Reviews ---
  async function getReviews() {
    if (demo) {
      liveReviewCount.value = fixtures.reviews.filter((r: any) => !r.reviewed).length
      return fixtures.reviews
    }

    const data = await request<any[]>('/api/admin/reviews')
    liveReviewCount.value = data.filter((r: any) => !r.reviewed).length
    return data
  }

  async function resolveReview(
    reviewId: string,
    decision = 'accept',
    note?: string,
    rewrittenText?: string,
  ) {
    if (demo) {
      liveReviewCount.value = Math.max(0, liveReviewCount.value - 1)
      return { status: 'ok', id: reviewId, reviewed: true, decision, note }
    }
    const res = await request<any>(`/api/admin/reviews/${encodeURIComponent(reviewId)}`, {
      method: 'PUT',
      body: JSON.stringify({
        decision,
        note: note || null,
        rewritten_text: rewrittenText || null,
      }),
    })
    liveReviewCount.value = Math.max(0, liveReviewCount.value - 1)
    return res
  }

  // --- System Configuration ---
  async function getConfig() {
    if (demo) {
      return {
        contact_name: 'PLACEHOLDER',
        contact_number: 'PLACEHOLDER',
        similarity_threshold: '0.72',
        rate_limit_per_hour: '30',
        session_ttl_hours: '24',
        retention_months: '12',
      }
    }

    return request<Record<string, string>>('/api/admin/config')
  }

  async function updateConfig(key: string, value: string) {
    if (demo) return { key, value }
    return request<any>(`/api/admin/config/${key}?value=${encodeURIComponent(value)}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    })
  }

  // --- Ingestion ---
  async function getIngestionStatus() {
    if (demo) {
      return {
        status: 'idle',
        sites_count: 5,
        articles_count: 1284,
        chunks_count: 9412,
        last_run_at: '2026-09-07T02:00:00Z',
      }
    }
    return request<any>('/api/admin/ingestion/status')
  }

  async function runIngestion() {
    if (demo) {
      return {
        status: 'completed',
        sites_count: 5,
        articles_count: 1284,
        chunks_count: 9412,
        last_run_at: new Date().toISOString(),
        audit_id: 'aud_demo_ingest',
      }
    }
    return request<any>('/api/admin/ingestion/run', {
      method: 'POST',
    })
  }

  // --- Admin Accounts ---
  async function getAdminAccounts() {
    if (demo) {
      return [
        { id: 'adm_1', email: 'siti@tanyaiman.id', role: 'editor', created_at: '' },
        { id: 'adm_2', email: 'budi@tanyaiman.id', role: 'reviewer', created_at: '' },
        { id: 'adm_3', email: 'admin@tanyaiman.id', role: 'super_admin', created_at: '' },
      ]
    }
    return request<any[]>('/api/admin/accounts')
  }

  async function createAdminAccount(email: string, password: string, role: string) {
    if (demo) {
      return { id: `adm_${Date.now()}`, email, role, created_at: new Date().toISOString() }
    }
    return request<any>('/api/admin/accounts', {
      method: 'POST',
      body: JSON.stringify({ email, password, role }),
    })
  }

  async function deleteAdminAccount(id: string) {
    if (demo) {
      return { status: 'ok', deleted_id: id }
    }
    return request<any>(`/api/admin/accounts/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  // --- Clusters ---
  async function getClusters(topicSlug?: string) {
    if (demo) return (fixtures as any).clusters || []

    const params = new URLSearchParams()
    if (topicSlug) params.set('topic', topicSlug)
    const data = await request<any[]>(`/api/admin/clusters?${params.toString()}`)
    return data.map((c: any) => ({
      id: c.id,
      canonical: c.canonical,
      count: c.count,
      topicSlug: c.topic_slug,
      topicLabel: c.topic_label,
      lastAsked: c.last_asked,
      hasCurated: c.has_curated,
      members: c.members || [],
    }))
  }

  async function renameCluster(clusterId: string, newCanonical: string) {
    return request<any>(`/api/admin/clusters/${clusterId}/rename`, {
      method: 'PUT',
      body: JSON.stringify({ new_canonical: newCanonical }),
    })
  }

  async function mergeCluster(targetId: string, sourceId: string) {
    return request<any>(`/api/admin/clusters/${targetId}/merge`, {
      method: 'POST',
      body: JSON.stringify({ source_cluster_id: sourceId }),
    })
  }

  async function promoteCluster(clusterId: string) {
    return request<any>(`/api/admin/clusters/${clusterId}/promote`, {
      method: 'POST',
    })
  }

  async function deleteCluster(clusterId: string) {
    return request<any>(`/api/admin/clusters/${clusterId}`, {
      method: 'DELETE',
    })
  }

  // --- Audit Log ---
  async function getAuditLogs(
    filters?:
      | number
      | {
          actor?: string
          action?: string
          dateFrom?: string
          dateTo?: string
          limit?: number
        },
  ) {
    if (demo) return fixtures.audit
    const params = new URLSearchParams()
    if (typeof filters === 'number') {
      params.set('limit', String(filters))
    } else {
      if (filters?.actor) params.set('actor', filters.actor)
      if (filters?.action) params.set('action', filters.action)
      if (filters?.dateFrom) params.set('date_from', filters.dateFrom)
      if (filters?.dateTo) params.set('date_to', filters.dateTo)
      params.set('limit', String(filters?.limit || 100))
    }
    const data = await request<any[]>(`/api/admin/audit?${params.toString()}`)
    return data.map((e: any) => ({
      id: e.id,
      actor: e.actor,
      action: e.action,
      target: e.target,
      detail: e.detail,
      at: e.at,
    }))
  }

  return {
    liveGapCount,
    liveReviewCount,
    getDashboard,
    getTopics,
    getTopic,
    updateTopicAnswer,
    getArticles,
    getQuestions,
    exportQuestionsCsv,
    getQuestionDetail,
    flagQuestion,
    deleteQuestion,
    getGaps,
    resolveGap,
    getReviews,
    resolveReview,
    getConfig,
    updateConfig,
    getIngestionStatus,
    runIngestion,
    getAdminAccounts,
    createAdminAccount,
    deleteAdminAccount,
    getClusters,
    renameCluster,
    mergeCluster,
    promoteCluster,
    deleteCluster,
    getAuditLogs,
  }
}
