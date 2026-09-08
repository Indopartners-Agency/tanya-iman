<script setup lang="ts">
/**
 * F-4 requires a Privacy Policy reachable from every screen. The published
 * policy lives at a Client-owned URL (SOW dependency B9, owner: Client/Legal)
 * and is not yet available, so this page states what the product does with
 * data and links out once that URL exists.
 */
const { t } = useCopy()
</script>

<template>
  <main class="min-h-dvh bg-base px-6 py-8">
    <div class="mx-auto max-w-measure">
      <NuxtLink
        to="/"
        class="mb-6 flex min-h-[44px] items-center gap-1.5 text-[14px] text-secondary"
      >
        <span aria-hidden="true">&#8592;</span> {{ t('ui.back') }}
      </NuxtLink>

      <h1 class="font-serif text-[28px] leading-tight text-primary">
        {{ t('ui.privacy') }}
      </h1>

      <div class="mt-6 space-y-4 text-[15px] leading-relaxed text-primary">
        <p>
          Tanya Iman menjawab pertanyaan tentang iman berdasarkan tulisan dari
          situs dialog keagamaan berbahasa Indonesia yang telah disetujui.
        </p>
        <p>
          Percakapan Anda disimpan di perangkat ini. Jika Anda masuk sebagai
          tamu, nomor telepon Anda tidak diminta dan tidak disimpan.
        </p>
        <p>
          Pertanyaan yang diajukan dicatat tanpa nomor telepon, agar tim kami
          dapat mengetahui bahan apa yang masih perlu disiapkan.
        </p>
        <p class="rounded-xl bg-info-bg px-4 py-3 text-info">
          Halaman ini adalah ringkasan sementara untuk keperluan pratinjau.
          Kebijakan Privasi resmi akan diterbitkan oleh klien pada alamat tetap
          sebelum peluncuran.
        </p>
      </div>
    </div>
  </main>
</template>
