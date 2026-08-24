/**
 * Wire types. These mirror backend/models/schemas.py exactly.
 *
 * Kept hand-written rather than generated so the diff is reviewable; the
 * contract test in the backend suite is what catches drift.
 */

export type Platform = 'web' | 'widget' | 'android'

export type AuthMethod = 'sms' | 'whatsapp' | 'guest'

export type AnswerSource =
  | 'curated'
  | 'generated'
  | 'refusal'
  | 'no_grounding'
  | 'crisis'
  | 'emotional_deferral'
  | 'error'

/** Mirrors AnswerSource.likeable in backend/models/enums.py. */
export const LIKEABLE_SOURCES: readonly AnswerSource[] = ['curated', 'generated']

export function isLikeable(source: AnswerSource): boolean {
  return LIKEABLE_SOURCES.includes(source)
}

export interface Citation {
  title: string
  url: string
  site: string
  article_id?: string | null
}

export interface CreateSessionRequest {
  platform: Platform
  embed_origin?: string | null
}

export interface CreateSessionResponse {
  session_id: string
}

export interface AskRequest {
  session_id: string
  text: string
}

export interface AskResponse {
  question_id: string
  answer_source: AnswerSource
  answer_text: string
  citations: Citation[]
  topic_slug: string | null
  likeable: boolean
  latency_ms: number
}

export interface LikeResponse {
  question_id: string
  liked: boolean
  like_count: number
}

export interface HealthResponse {
  status: string
  env: string
  prompt_version: string
  corpus_chunk_count: number
  engine: string
}
