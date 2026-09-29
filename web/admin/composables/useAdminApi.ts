import { useSessionStore } from '~/stores/session'
import * as fixtures from '~/demo/fixtures'

export function useAdminApi() {
  const config = useRuntimeConfig()
  const session = useSessionStore()
  const router = useRouter()
  const demo = useDemoMode()

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

    if (res.status === 401 && session.refreshToken) {
      // Try refresh token once
      const newToken = await session.refresh()
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`)
        res = await fetch(url, { ...options, headers })
      } else {
        session.signOut()
        await router.push('/masuk')
        throw new Error('Sesi berakhir. Silakan masuk kembali.')
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      const detail = typeof err?.detail === 'string' ? err.detail : `Permintaan gagal (${res.status})`
      throw new Error(detail)
    }

    return res.json() as Promise<T>
  }

  // --- Dashboard ---
  async function getDashboard() {
    if (demo) {
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

    try {
      const data = await request<any>('/api/admin/dashboard')
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
        validator_pass_pct: 100,
        answer_rate_pct: 100,
        like_rate_pct: data.total_questions > 0 ? Math.round((data.total_likes / data.total_questions) * 100) : 0,
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
          refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : (t.refusal_rate || 0),
        })),
        largest_gap: null,
      }
    } catch (e) {
      console.warn('Failed to load dashboard from API, using fixtures:', e)
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
  }

  // --- Topics ---
  async function getTopics() {
    if (demo) return fixtures.topics

    try {
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
        curatedCitations: t.curated_citations,
        refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : (t.refusal_rate || 0),
      }))
    } catch (e) {
      console.warn('Failed to load topics from API, using fixtures:', e)
      return fixtures.topics
    }
  }

  async function getTopic(slug: string) {
    if (demo) return fixtures.topics.find((t) => t.slug === slug) || null

    try {
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
        curatedCitations: t.curated_citations,
        refusalRate: (t.refusal_rate || 0) > 1 ? t.refusal_rate / 100 : (t.refusal_rate || 0),
      }
    } catch (e) {
      console.warn(`Failed to load topic ${slug} from API, using fixtures:`, e)
      return fixtures.topics.find((t) => t.slug === slug) || null
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

  // --- Questions ---
  async function getQuestions(filters?: { topic?: string; result?: string; search?: string }) {
    if (demo) return fixtures.questions

    try {
      const params = new URLSearchParams()
      if (filters?.topic) params.set('topic', filters.topic)
      if (filters?.result) params.set('source', filters.result)
      params.set('limit', '100')

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
    } catch (e) {
      console.warn('Failed to load questions from API, using fixtures:', e)
      return fixtures.questions
    }
  }

  async function getQuestionDetail(id: string) {
    if (demo) return fixtures.questions.find((q) => q.id === id) || null

    try {
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
        citations: q.citations || [],
        retrievedChunkIds: q.retrieved_chunk_ids || [],
        validatorFailures: q.validator_failures || [],
        model: q.model,
        promptVersion: q.prompt_version,
        latencyMs: q.latency_ms,
      }
    } catch (e) {
      console.warn(`Failed to load question ${id} from API, using fixtures:`, e)
      return fixtures.questions.find((q) => q.id === id) || null
    }
  }

  // --- Gaps ---
  async function getGaps() {
    if (demo) return fixtures.gaps

    try {
      const data = await request<any[]>('/api/admin/gaps')
      return data.length > 0 ? data : fixtures.gaps
    } catch (e) {
      console.warn('Failed to load gaps from API, using fixtures:', e)
      return fixtures.gaps
    }
  }

  // --- Reviews ---
  async function getReviews() {
    if (demo) return fixtures.reviews

    try {
      const data = await request<any[]>('/api/admin/reviews')
      return data.length > 0 ? data : fixtures.reviews
    } catch (e) {
      console.warn('Failed to load reviews from API, using fixtures:', e)
      return fixtures.reviews
    }
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

    try {
      return await request<Record<string, string>>('/api/admin/config')
    } catch (e) {
      console.warn('Failed to load config from API, using defaults:', e)
      return {
        contact_name: 'PLACEHOLDER',
        contact_number: 'PLACEHOLDER',
        similarity_threshold: '0.72',
        rate_limit_per_hour: '30',
        session_ttl_hours: '24',
        retention_months: '12',
      }
    }
  }

  async function updateConfig(key: string, value: string) {
    if (demo) return { key, value }
    return request<any>(`/api/admin/config/${key}?value=${encodeURIComponent(value)}`, {
      method: 'PUT',
    })
  }

  // --- Clusters ---
  async function getClusters(topicSlug?: string) {
    if (demo) return (fixtures as any).clusters || []

    try {
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
    } catch (e) {
      console.warn('Failed to load clusters from API:', e)
      return (fixtures as any).clusters || []
    }
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

  // --- Audit Log ---
  async function getAuditLogs(limit = 100) {
    try {
      const data = await request<any[]>(`/api/admin/audit?limit=${limit}`)
      return data.map((e: any) => ({
        id: e.id,
        actor: e.actor,
        action: e.action,
        target: e.target,
        detail: e.detail,
        at: e.at,
      }))
    } catch (e) {
      console.warn('Failed to load audit logs from API:', e)
      return []
    }
  }

  return {
    getDashboard,
    getTopics,
    getTopic,
    updateTopicAnswer,
    getQuestions,
    getQuestionDetail,
    getGaps,
    getReviews,
    getConfig,
    updateConfig,
    getClusters,
    renameCluster,
    mergeCluster,
    promoteCluster,
    getAuditLogs,
  }
}
