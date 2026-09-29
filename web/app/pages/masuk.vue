<script setup lang="ts">
/**
 * Chat UX section 6. Phone entry, then OTP, in one route driven by `?channel=`.
 *
 * The two steps share a route because a back affordance from OTP has to return
 * to phone entry without losing the number, and nothing has been committed
 * server-side until the code is verified.
 *
 * Real verification is Phase 3 (PIP 3.1-3.3). In demo mode any six digits are
 * accepted, so a reviewer can walk the whole flow.
 */
const { t } = useCopy()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const demo = useDemoMode()

const channel = computed(() => (route.query.channel === 'whatsapp' ? 'whatsapp' : 'sms'))

const step = ref<'phone' | 'otp'>('phone')
const phone = ref('')
const digits = ref<string[]>(Array(6).fill(''))
const inputs = ref<HTMLInputElement[]>([])
const touched = ref(false)
const error = ref<string | null>(null)
const busy = ref(false)

/** Section 6.1: validation only after blur, never while they are still typing. */
const phoneValid = computed(() => /^8[1-9][0-9]{7,11}$/.test(phone.value.replace(/\D/g, '')))
const showPhoneError = computed(() => touched.value && phone.value.length > 0 && !phoneValid.value)

const RESEND_SECONDS = 60
const resendIn = ref(0)
let ticker: ReturnType<typeof setInterval> | undefined

function startResendCountdown() {
  resendIn.value = RESEND_SECONDS
  if (ticker) clearInterval(ticker)
  ticker = setInterval(() => {
    resendIn.value = Math.max(0, resendIn.value - 1)
    if (resendIn.value === 0 && ticker) clearInterval(ticker)
  }, 1000)
}

onUnmounted(() => {
  if (ticker) clearInterval(ticker)
})

async function sendCode() {
  if (!phoneValid.value) {
    touched.value = true
    return
  }
  error.value = null
  step.value = 'otp'
  startResendCountdown()
  await nextTick()
  inputs.value[0]?.focus()
}

function onDigit(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  const value = input.value.replace(/\D/g, '')

  // Paste of a full code fills every box rather than only the one focused.
  if (value.length > 1) {
    const chars = value.slice(0, 6).split('')
    chars.forEach((char, offset) => {
      if (index + offset < 6) digits.value[index + offset] = char
    })
    const next = Math.min(index + chars.length, 5)
    inputs.value[next]?.focus()
    maybeSubmit()
    return
  }

  digits.value[index] = value
  if (value && index < 5) inputs.value[index + 1]?.focus()
  maybeSubmit()
}

function onBackspace(index: number) {
  if (digits.value[index]) return
  if (index > 0) inputs.value[index - 1]?.focus()
}

const digitsComplete = computed(() => digits.value.every((d) => d !== ''))

/** Section 6.2: auto-submit on the sixth character; no separate confirm tap. */
function maybeSubmit() {
  if (digitsComplete.value) verify()
}

async function verify() {
  busy.value = true
  error.value = null
  try {
    if (demo) {
      await auth.signInAsGuest()
      await router.push('/chat')
      return
    }
    // Phase 3 wires the real provider here.
    error.value = t('ui.otp_invalid')
  } catch (err: any) {
    error.value = err?.message || t('ui.otp_invalid')
  } finally {
    busy.value = false
  }
}

async function bypassDemo() {
  busy.value = true
  try {
    await auth.signInAsGuest()
    await router.push('/chat')
  } catch (err: any) {
    error.value = err?.message || 'Gagal masuk demo'
  } finally {
    busy.value = false
  }
}

function back() {
  if (step.value === 'otp') {
    step.value = 'phone'
    digits.value = Array(6).fill('')
    return
  }
  router.push('/')
}
</script>

<template>
  <main class="flex min-h-dvh flex-col bg-base px-6">
    <header class="py-4">
      <button
        type="button"
        class="flex min-h-[44px] items-center gap-1.5 text-[14px] text-secondary"
        @click="back"
      >
        <span aria-hidden="true">&#8592;</span> {{ t('ui.back') }}
      </button>
    </header>

    <div class="flex flex-1 flex-col justify-center pb-16">
      <div class="mx-auto w-full max-w-[400px]">
        <!-- Phone entry -->
        <template v-if="step === 'phone'">
          <div v-if="demo" class="mb-5 rounded-xl border border-info/30 bg-info-bg p-3.5 text-[13px] text-info">
            <p class="font-medium">Mode Demo</p>
            <p class="mt-1 text-info/90">Gunakan nomor telepon apa saja untuk mencoba alur, atau lewati langsung ke obrolan.</p>
            <button
              type="button"
              class="mt-2.5 inline-flex min-h-[36px] items-center rounded-lg bg-info px-3 text-[12.5px] font-medium text-surface transition hover:opacity-90"
              @click="bypassDemo"
            >
              Lewati ke Chat (Demo) &rarr;
            </button>
          </div>

          <h1 class="font-serif text-[26px] leading-tight text-primary">
            {{ channel === 'whatsapp' ? t('ui.login_whatsapp') : t('ui.login_sms') }}
          </h1>

          <label for="phone" class="mt-8 block text-[14px] font-medium text-primary">
            {{ t('ui.phone_label') }}
          </label>
          <div
            class="mt-2 flex items-stretch overflow-hidden rounded-xl border border-strong bg-surface focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/15"
          >
            <span
              class="grid place-items-center border-r border-subtle bg-raised px-3 text-[15px] text-secondary"
            >
              +62
            </span>
            <input
              id="phone"
              v-model="phone"
              type="tel"
              inputmode="numeric"
              autocomplete="tel-national"
              :placeholder="t('ui.phone_placeholder')"
              class="min-h-[52px] w-full bg-transparent px-3 text-[15px] text-primary outline-none placeholder:text-secondary"
              @blur="touched = true"
            />
          </div>
          <p v-if="showPhoneError" class="mt-2 text-[13px] text-warning">
            {{ t('ui.phone_invalid') }}
          </p>

          <button
            type="button"
            class="mt-6 min-h-[52px] w-full rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
            :disabled="!phoneValid"
            @click="sendCode"
          >
            Kirim kode
          </button>
        </template>

        <!-- OTP entry -->
        <template v-else>
          <div v-if="demo" class="mb-5 rounded-xl border border-info/30 bg-info-bg p-3.5 text-[13px] text-info">
            <p class="font-medium">Mode Demo</p>
            <p class="mt-1 text-info/90">Masukkan 6 digit angka apa saja (misal: 000000) atau klik tombol di bawah untuk langsung masuk.</p>
            <button
              type="button"
              class="mt-2.5 inline-flex min-h-[36px] items-center rounded-lg bg-info px-3 text-[12.5px] font-medium text-surface transition hover:opacity-90"
              @click="bypassDemo"
            >
              Masuk Langsung (Demo) &rarr;
            </button>
          </div>

          <h1 class="font-serif text-[26px] leading-tight text-primary">
            {{ t('ui.otp_title') }}
          </h1>
          <p class="mt-2 text-[14px] text-secondary">
            {{ t('ui.otp_sent_to', { phone: `+62${phone}` }) }}
          </p>

          <div class="mt-8 flex justify-between gap-2" role="group" :aria-label="t('ui.otp_label')">
            <input
              v-for="(_, index) in digits"
              :key="index"
              :ref="(el) => { if (el) inputs[index] = el as HTMLInputElement }"
              v-model="digits[index]"
              type="text"
              inputmode="numeric"
              maxlength="6"
              :aria-label="`${t('ui.otp_label')} ${index + 1}`"
              class="h-14 w-full rounded-xl border border-strong bg-surface text-center font-mono text-[20px] text-primary outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
              @input="onDigit(index, $event)"
              @keydown.backspace="onBackspace(index)"
              @keydown.enter="maybeSubmit"
            />
          </div>

          <button
            type="button"
            class="mt-6 min-h-[52px] w-full rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
            :disabled="!digitsComplete || busy"
            @click="verify"
          >
            {{ busy ? 'Memverifikasi...' : 'Verifikasi kode' }}
          </button>

          <p v-if="error" class="mt-3 text-[13px] text-warning">{{ error }}</p>

          <div class="mt-6 flex items-center justify-between">
            <button
              type="button"
              class="min-h-[44px] text-[14px] text-accent underline underline-offset-2 disabled:text-secondary disabled:no-underline"
              :disabled="resendIn > 0 || busy"
              @click="startResendCountdown"
            >
              {{ resendIn > 0 ? t('ui.otp_resend_in', { seconds: resendIn }) : t('ui.otp_resend') }}
            </button>
            <button
              type="button"
              class="min-h-[44px] text-[14px] text-secondary underline underline-offset-2"
              @click="back"
            >
              {{ t('ui.otp_change_number') }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <footer class="py-4 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </main>
</template>
