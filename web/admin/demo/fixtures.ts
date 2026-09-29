import type { AnswerSource, Platform } from '@tanya-iman/shared'

/**
 * DEMO DATA — NOT REAL. Backs the hosted approval build so the editorial team
 * can review the portal before Phase 6 connects it to the API.
 *
 * Deleted wholesale when the real admin endpoints land.
 *
 * Question texts are invented and no phone number appears anywhere, in keeping
 * with Admin UX section 7.4 — the list view has no phone column at all.
 */

export interface QuestionRow {
  id: string
  askedAt: string
  question: string
  topicSlug: string
  topicLabel: string
  result: AnswerSource
  likes: number
  channel: Platform
  hostSite?: string
  flags: Array<'ambiguous' | 'validator' | 'injection'>
}

export interface TopicRow {
  slug: string
  label: string
  questions: number
  likes: number
  curated: 'none' | 'draft' | 'published'
  curatedBy?: string
  curatedAt?: string
  curatedAnswer?: string
  curatedCitations?: any[]
  refusalRate: number
}

export interface ClusterRow {
  id: string
  canonical: string
  count: number
  topicLabel: string
  lastAsked: string
  hasCurated: boolean
  members: string[]
}

export interface GapRow {
  id: string
  canonical: string
  count: number
  lastAsked: string
  nearestTopic: string
}

export interface ReviewRow {
  id: string
  type: 'ambiguous' | 'validator' | 'crisis' | 'emotional'
  summary: string
  at: string
  reviewed: boolean
}

export interface AuditRow {
  id: string
  actor: string
  action: string
  target: string
  at: string
}

export const questions: QuestionRow[] = [
  {
    id: 'q_1041',
    askedAt: '2026-09-08T09:14:00+07:00',
    question: 'Siapakah Isa Al-Masih menurut Kitab Suci?',
    topicSlug: 'identitas-isa',
    topicLabel: 'Identitas Isa Al-Masih',
    result: 'generated',
    likes: 3,
    channel: 'web',
    flags: [],
  },
  {
    id: 'q_1040',
    askedAt: '2026-09-08T08:52:00+07:00',
    question: 'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
    topicSlug: 'pengampunan',
    topicLabel: 'Pengampunan',
    result: 'curated',
    likes: 11,
    channel: 'widget',
    hostSite: 'isadanislam.org',
    flags: [],
  },
  {
    id: 'q_1039',
    askedAt: '2026-09-08T08:31:00+07:00',
    question: 'Bagaimana pandangan Kitab Suci tentang penambangan aset kripto?',
    topicSlug: 'lainnya',
    topicLabel: 'Lainnya',
    result: 'no_grounding',
    likes: 0,
    channel: 'android',
    flags: [],
  },
  {
    id: 'q_1038',
    askedAt: '2026-09-08T07:58:00+07:00',
    question: 'Bagaimana Isa Al-Masih memperlakukan perempuan?',
    topicSlug: 'perempuan',
    topicLabel: 'Perempuan dan Keluarga',
    result: 'generated',
    likes: 7,
    channel: 'widget',
    hostSite: 'isaislamdankaumwanita.com',
    flags: [],
  },
  {
    id: 'q_1037',
    askedAt: '2026-09-07T21:12:00+07:00',
    question: 'Apakah benar semua orang akan masuk neraka?',
    topicSlug: 'akhirat',
    topicLabel: 'Akhirat',
    result: 'generated',
    likes: 2,
    channel: 'web',
    flags: ['ambiguous'],
  },
  {
    id: 'q_1036',
    askedAt: '2026-09-07T20:40:00+07:00',
    question: 'Tolong buatkan saya kode Python untuk mengurutkan daftar.',
    topicSlug: 'lainnya',
    topicLabel: 'Lainnya',
    result: 'refusal',
    likes: 0,
    channel: 'web',
    flags: [],
  },
  {
    id: 'q_1035',
    askedAt: '2026-09-07T19:03:00+07:00',
    question: 'Apa maksud kasih karunia dalam Injil?',
    topicSlug: 'keselamatan',
    topicLabel: 'Keselamatan',
    result: 'generated',
    likes: 5,
    channel: 'android',
    flags: ['validator'],
  },
  {
    id: 'q_1034',
    askedAt: '2026-09-07T16:22:00+07:00',
    question: 'Mengapa Kitab Suci disebut tidak berubah?',
    topicSlug: 'kitab-suci',
    topicLabel: 'Kitab Suci',
    result: 'generated',
    likes: 4,
    channel: 'widget',
    hostSite: 'isadanalquran.com',
    flags: [],
  },
]

export const topics: TopicRow[] = [
  { slug: 'identitas-isa', label: 'Identitas Isa Al-Masih', questions: 412, likes: 96, curated: 'published', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-08-30', refusalRate: 0.04 },
  { slug: 'pengampunan', label: 'Pengampunan', questions: 318, likes: 141, curated: 'published', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-09-01', refusalRate: 0.06 },
  { slug: 'keselamatan', label: 'Keselamatan', questions: 276, likes: 72, curated: 'draft', curatedBy: 'budi@tanyaiman.id', curatedAt: '2026-09-05', refusalRate: 0.09 },
  { slug: 'kitab-suci', label: 'Kitab Suci', questions: 244, likes: 61, curated: 'none', refusalRate: 0.12 },
  { slug: 'akhirat', label: 'Akhirat', questions: 198, likes: 44, curated: 'none', refusalRate: 0.18 },
  { slug: 'doa', label: 'Doa', questions: 163, likes: 39, curated: 'published', curatedBy: 'budi@tanyaiman.id', curatedAt: '2026-08-24', refusalRate: 0.07 },
  { slug: 'perempuan', label: 'Perempuan dan Keluarga', questions: 149, likes: 58, curated: 'none', refusalRate: 0.11 },
  { slug: 'nabi', label: 'Para Nabi', questions: 131, likes: 27, curated: 'none', refusalRate: 0.14 },
  { slug: 'salib', label: 'Salib dan Penebusan', questions: 118, likes: 33, curated: 'draft', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-09-03', refusalRate: 0.16 },
  { slug: 'roh', label: 'Roh dan Kehidupan Kekal', questions: 97, likes: 21, curated: 'none', refusalRate: 0.19 },
  { slug: 'ibadah', label: 'Ibadah', questions: 84, likes: 18, curated: 'none', refusalRate: 0.1 },
  { slug: 'keraguan', label: 'Keraguan', questions: 76, likes: 29, curated: 'none', refusalRate: 0.22 },
  { slug: 'komunitas', label: 'Komunitas dan Ibadah Bersama', questions: 54, likes: 12, curated: 'none', refusalRate: 0.13 },
  { slug: 'lainnya', label: 'Lainnya', questions: 208, likes: 9, curated: 'none', refusalRate: 0.41 },
]

export const clusters: ClusterRow[] = [
  {
    id: 'c_1',
    canonical: 'Apakah dosa saya masih bisa diampuni?',
    count: 87,
    topicLabel: 'Pengampunan',
    lastAsked: '2026-09-08T08:52:00+07:00',
    hasCurated: true,
    members: [
      'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
      'Dosa saya terlalu banyak, apakah masih ada harapan?',
      'Bisakah orang seperti saya diampuni?',
    ],
  },
  {
    id: 'c_2',
    canonical: 'Siapa sebenarnya Isa Al-Masih?',
    count: 74,
    topicLabel: 'Identitas Isa Al-Masih',
    lastAsked: '2026-09-08T09:14:00+07:00',
    hasCurated: true,
    members: [
      'Siapakah Isa Al-Masih menurut Kitab Suci?',
      'Apakah Isa hanya seorang nabi?',
      'Mengapa Isa disebut Firman Allah?',
    ],
  },
  {
    id: 'c_3',
    canonical: 'Mengapa Kitab Suci dianggap tidak berubah?',
    count: 41,
    topicLabel: 'Kitab Suci',
    lastAsked: '2026-09-07T16:22:00+07:00',
    hasCurated: false,
    members: [
      'Mengapa Kitab Suci disebut tidak berubah?',
      'Bukankah Injil sudah diubah manusia?',
    ],
  },
]

export const gaps: GapRow[] = [
  { id: 'g_1', canonical: 'Bagaimana pandangan Kitab Suci tentang keuangan dan utang?', count: 34, lastAsked: '2026-09-08T08:31:00+07:00', nearestTopic: 'Lainnya' },
  { id: 'g_2', canonical: 'Apa kata Kitab Suci tentang mimpi dan tafsirnya?', count: 27, lastAsked: '2026-09-07T14:10:00+07:00', nearestTopic: 'Lainnya' },
  { id: 'g_3', canonical: 'Bagaimana menghadapi tekanan keluarga soal keyakinan?', count: 22, lastAsked: '2026-09-06T19:45:00+07:00', nearestTopic: 'Komunitas dan Ibadah Bersama' },
  { id: 'g_4', canonical: 'Apakah ada penjelasan tentang kehidupan setelah kematian bagi anak?', count: 15, lastAsked: '2026-09-05T11:02:00+07:00', nearestTopic: 'Akhirat' },
]

export const reviews: ReviewRow[] = [
  { id: 'r_1', type: 'validator', summary: 'V1_TOO_LONG — 271 kata pada jawaban q_1035', at: '2026-09-07T19:04:00+07:00', reviewed: false },
  { id: 'r_2', type: 'ambiguous', summary: 'Klasifikasi ambigu antara teologi dan emosional — q_1037', at: '2026-09-07T21:13:00+07:00', reviewed: false },
  { id: 'r_3', type: 'crisis', summary: 'Peristiwa krisis terdeteksi — rutin ditinjau bulanan (K9)', at: '2026-09-06T23:41:00+07:00', reviewed: false },
  { id: 'r_4', type: 'emotional', summary: 'Penangguhan emosional — periksa tampilan nomor kontak', at: '2026-09-06T10:18:00+07:00', reviewed: true },
]

export const audit: AuditRow[] = [
  { id: 'a_912', actor: 'siti@tanyaiman.id', action: 'Menerbitkan jawaban kurasi', target: 'Topik: Pengampunan', at: '2026-09-01T10:22:00+07:00' },
  { id: 'a_911', actor: 'admin@tanyaiman.id', action: 'Menonaktifkan akun', target: 'rina@tanyaiman.id', at: '2026-08-29T15:40:00+07:00' },
  { id: 'a_910', actor: 'siti@tanyaiman.id', action: 'Menghapus pertanyaan', target: 'q_0987', at: '2026-08-28T09:05:00+07:00' },
]

/** Dashboard numbers. Validator rate is deliberately below 100% so the client
 *  sees what the K4 alert state looks like — Admin UX section 6. */
export const dashboard = {
  volumeThisWeek: 1284,
  volumeChangePct: 12,
  answerRatePct: 91,
  likeRatePct: 34,
  validatorPassPct: 99.2,
}

export const gapCount = gaps.length
export const reviewCount = reviews.filter((r) => !r.reviewed).length

/** Articles the citation picker searches. Approved sites only — Admin UX 10. */
export const articles = [
  { id: 'art_1', title: 'Siapakah Isa Al-Masih dalam Injil?', site: 'isadanislam.org', url: 'https://isadanislam.org/siapakah-isa-al-masih/' },
  { id: 'art_2', title: 'Firman yang Menjadi Manusia', site: 'isadanalquran.com', url: 'https://isadanalquran.com/firman-yang-menjadi-manusia/' },
  { id: 'art_3', title: 'Pengampunan yang Tidak Terbatas', site: 'isadanalfatihah.com', url: 'https://isadanalfatihah.com/pengampunan-yang-tidak-terbatas/' },
  { id: 'art_4', title: 'Perempuan dalam Pandangan Isa Al-Masih', site: 'isaislamdankaumwanita.com', url: 'https://isaislamdankaumwanita.com/perempuan-dalam-pandangan-isa/' },
  { id: 'art_5', title: 'Ia Tidak Menghukum', site: 'takutneraka.com', url: 'https://takutneraka.com/ia-tidak-menghukum/' },
  { id: 'art_6', title: 'Kasih yang Tidak Berkesudahan', site: 'isadanislam.org', url: 'https://isadanislam.org/kasih-yang-tidak-berkesudahan/' },
]

/** Retrieved chunks for the question detail page's diagnostics panel. */
export const retrievedChunks = [
  { id: 'ch_1', articleTitle: 'Siapakah Isa Al-Masih dalam Injil?', site: 'isadanislam.org', score: 0.89, cited: true, text: 'Injil membuka dengan pernyataan bahwa Firman itu telah ada pada mulanya, dan Firman itu bersama-sama dengan Allah…' },
  { id: 'ch_2', articleTitle: 'Firman yang Menjadi Manusia', site: 'isadanalquran.com', score: 0.84, cited: true, text: 'Firman itu telah menjadi manusia dan diam di antara kita, penuh kasih karunia dan kebenaran…' },
  { id: 'ch_3', articleTitle: 'Kasih yang Tidak Berkesudahan', site: 'isadanislam.org', score: 0.71, cited: false, text: 'Kasih Allah tidak diukur dari kelayakan manusia, melainkan dari sifat Allah sendiri…' },
]

/** V1–V5 results for the diagnostics panel. */
export const validators = [
  { code: 'V1', label: 'Panjang', pass: true, measured: '184 kata' },
  { code: 'V2', label: 'Sebutan', pass: true, measured: 'Allah, Isa Al-Masih' },
  { code: 'V3', label: 'Keseimbangan ayat', pass: true, measured: '1 rujukan Quran, 2 rujukan Kitab Suci' },
  { code: 'V4', label: 'Sumber kutipan', pass: true, measured: '2 tautan, keduanya dari situs disetujui' },
  { code: 'V5', label: 'Dasar jawaban', pass: true, measured: 'Seluruh klaim tertaut ke potongan yang diambil' },
]
