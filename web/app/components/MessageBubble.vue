<script setup lang="ts">
import type { Message } from '~/stores/chat'

/**
 * Selects a treatment on answer_source (Chat UX section 8) and hands the
 * non-standard states to AnswerStates. A curated answer renders identically to
 * a generated one — deliberately. The seeker is never told which they got.
 */
const props = defineProps<{ message: Message }>()
defineEmits<{ like: [questionId: string]; retry: [id: string] }>()

const isSeeker = computed(() => props.message.role === 'seeker')

const STANDARD: Array<string | undefined> = ['generated', 'curated', undefined]
const isStandard = computed(
  () => !props.message.pending && STANDARD.includes(props.message.answerSource),
)
</script>

<template>
  <div :class="['flex w-full', isSeeker ? 'justify-end' : 'justify-start']">
    <!-- Seeker's own message. -->
    <div
      v-if="isSeeker"
      class="max-w-[85%] rounded-2xl rounded-br-md bg-bubble-user px-4 py-3 text-[15px] leading-relaxed text-on-accent"
    >
      <p class="whitespace-pre-wrap">{{ message.text }}</p>
    </div>

    <!-- Pending. -->
    <div
      v-else-if="message.pending"
      class="max-w-[90%] rounded-2xl rounded-bl-md border border-subtle bg-bubble-assistant px-4 py-3 shadow-sm"
    >
      <PendingBubble />
    </div>

    <!-- Standard answer: generated or curated, rendered the same way. -->
    <div
      v-else-if="isStandard"
      class="max-w-[90%] rounded-2xl rounded-bl-md border border-subtle bg-bubble-assistant px-4 py-3.5 text-[15px] leading-relaxed text-primary shadow-sm"
    >
      <p class="whitespace-pre-wrap">{{ message.text }}</p>

      <CitationList v-if="message.citations?.length" :citations="message.citations" />

      <LikeControl
        v-if="message.likeable && message.questionId"
        :liked="Boolean(message.liked)"
        @toggle="$emit('like', message.questionId!)"
      />
    </div>

    <!-- Refusal, no-grounding, crisis, rate limit, error. -->
    <div v-else class="max-w-[90%]">
      <AnswerStates :message="message" @retry="$emit('retry', $event)" />
    </div>
  </div>
</template>
