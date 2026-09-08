<script setup lang="ts">
/**
 * A stand-in for one of the five approved host sites, so the widget can be
 * reviewed in context. The iframe URL matches what public/embed.js loads:
 * hash routing, because the widget is served from a static bundle where a
 * deep path would 404 on refresh.
 *
 * Chat UX section 11: inside the frame the header and outer background are
 * suppressed while the source note and privacy link remain, because F-4 and
 * F-6 apply in the widget exactly as they do in the app.
 */
useHead({ title: 'Pratinjau Widget — Tanya Iman' })

const frame = ref<HTMLIFrameElement | null>(null)
const height = ref(620)

/**
 * The widget reports its height so the host page can size the frame instead of
 * scrolling inside a fixed box. Same message shape as public/embed.js.
 */
function onMessage(event: MessageEvent) {
  if (event.data?.type !== 'tanya-iman:height') return
  const next = Number(event.data.height)
  if (Number.isFinite(next) && next > 0) height.value = next
}

onMounted(() => window.addEventListener('message', onMessage))
onUnmounted(() => window.removeEventListener('message', onMessage))
</script>

<template>
  <!-- Deliberately not the Tanya Iman palette: this is somebody else's website,
       and the point of the page is to show the widget sitting inside one. -->
  <div style="background: #ffffff; color: #23282d; font-family: Georgia, serif">
    <header style="border-bottom: 1px solid #e5e5e5">
      <div style="margin: 0 auto; max-width: 1100px; padding: 18px 24px">
        <p style="font-size: 20px; font-weight: 700; letter-spacing: -0.01em">Isa dan Islam</p>
      </div>
    </header>

    <div
      style="margin: 0 auto; display: grid; max-width: 1100px; gap: 40px; padding: 32px 24px 64px; grid-template-columns: minmax(0, 1fr) 360px"
    >
      <article>
        <h1 style="margin: 0 0 8px; font-size: 32px; line-height: 1.25">
          Mengapa Isa Al-Masih Disebut Firman Allah?
        </h1>
        <p style="margin: 0 0 24px; font-size: 13px; color: #767676">
          Artikel contoh &middot; 8 September 2026
        </p>

        <div style="font-size: 17px; line-height: 1.75; color: #33383d">
          <p style="margin: 0 0 18px">
            Pertanyaan ini sering muncul dalam percakapan sehari-hari, dan
            jawabannya tidak sesederhana yang diduga banyak orang. Halaman ini
            adalah contoh artikel milik situs klien, dipakai untuk memperlihatkan
            bagaimana widget Tanya Iman tampil di dalamnya.
          </p>
          <p style="margin: 0 0 18px">
            Widget di sebelah kanan memuat aplikasi yang sama dengan versi web
            dan Android, dalam mode tersemat. Kolom isi situs berbeda-beda di
            kelima situs yang disetujui, sehingga tata letaknya harus tetap utuh
            hingga lebar 320 piksel.
          </p>
          <p style="margin: 0">
            Tautan bacaan di dalam widget terbuka di jendela utama, bukan di
            dalam bingkai — pembaca yang menekan tautan tidak boleh kehilangan
            percakapannya.
          </p>
        </div>
      </article>

      <aside>
        <p
          style="margin: 0 0 10px; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #767676"
        >
          Tanya Iman
        </p>
        <iframe
          ref="frame"
          src="./#/chat?embed=1"
          title="Tanya Iman"
          :style="{
            width: '100%',
            height: `${height}px`,
            border: '1px solid #e0dbc9',
            borderRadius: '12px',
            background: '#fffdf7',
          }"
        />
      </aside>
    </div>
  </div>
</template>
