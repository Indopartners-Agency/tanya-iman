import {
  ApiError,
  isLikeable,
  type ApiClient,
  type AskRequest,
  type AskResponse,
  type CreateSessionRequest,
  type CreateSessionResponse,
  type HealthResponse,
  type LikeResponse,
} from '@tanya-iman/shared'
import { pickScenario, type DemoScenario } from '~/demo/scenarios'

/**
 * A fixture-backed ApiClient for the hosted approval build.
 *
 * Deleted in Phase 5 along with demo/scenarios.ts and useDemoMode.ts — this is
 * the entire footprint of demo mode outside those two files.
 *
 * It reproduces the behaviours the UI has to handle, not just the happy path:
 * a realistic delay so the pending state is visible, a 429 that carries
 * Retry-After so the countdown has something to count, and a thrown error so
 * the retry affordance can be exercised.
 */

/** Long enough that the pending state is visibly real, short enough to demo. */
const LATENCY_MS = 1400

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

let counter = 0

/** Overridden by the scenario bar so a reviewer can force any state. */
let forced: DemoScenario | null = null

export function forceScenario(scenario: DemoScenario | null): void {
  forced = scenario
}

export function createDemoClient(): ApiClient {
  const likes = new Map<string, boolean>()

  return {
    health: async (): Promise<HealthResponse> => ({
      status: 'ok',
      env: 'demo',
      prompt_version: 'demo',
      corpus_chunk_count: 0,
      engine: 'demo',
    }),

    createSession: async (
      _payload: CreateSessionRequest,
    ): Promise<CreateSessionResponse> => {
      await delay(150)
      return { session_id: `demo_session_${Date.now()}` }
    },

    ask: async (payload: AskRequest): Promise<AskResponse> => {
      await delay(LATENCY_MS)

      const scenario = forced ?? pickScenario(payload.text)

      // Rate limit is an HTTP condition, not an answer_source, so it has to be
      // thrown rather than returned — the store branches on ApiError.
      if (scenario.retryAfterSeconds) {
        throw new ApiError(429, 'rate limited', scenario.retryAfterSeconds)
      }

      if (scenario.answerSource === 'error') {
        throw new ApiError(503, 'demo failure')
      }

      counter += 1
      return {
        question_id: `demo_q_${counter}`,
        answer_source: scenario.answerSource,
        // Template states render copy from id.json, so the body is empty here
        // and the component selects on answer_source.
        answer_text: scenario.answerText ?? '',
        citations: scenario.citations,
        topic_slug: null,
        likeable: isLikeable(scenario.answerSource),
        latency_ms: LATENCY_MS,
      }
    },

    like: async (questionId: string, liked: boolean): Promise<LikeResponse> => {
      await delay(200)
      likes.set(questionId, liked)
      return { question_id: questionId, liked, like_count: liked ? 1 : 0 }
    },
  }
}
