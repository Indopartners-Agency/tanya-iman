import type { AnswerSource, Citation } from '@tanya-iman/shared'

/**
 * Sample content for the hosted approval build.
 *
 * DEMO CONTENT — NOT EDITORIALLY APPROVED. These answer bodies were written to
 * demonstrate layout, tone, and citation rendering. They are not the product's
 * answers; Phase 5 produces those from the corpus, and the editorial team
 * approves prompts and refusal copy under SOW dependencies B2 and B8.
 *
 * Template strings (greeting, refusal, no-grounding, rate limit, error) are NOT
 * written here — they come from locales/id.json, which is byte-identical to
 * backend/config/responses.id.yml and asserted by test_copy_parity.py.
 *
 * The crisis scenario deliberately carries no real helpline number. The crisis
 * script is owned by the client's pastoral staff (SOW B1) and is unapproved.
 */

export interface DemoScenario {
  /** Shown in the demo scenario bar. */
  label: string
  question: string
  answerSource: AnswerSource
  /** Omitted for template-driven states, which read their copy from id.json. */
  answerText?: string
  citations: Citation[]
  /** Only for the rate-limit scenario. */
  retryAfterSeconds?: number
}

const ISA_DAN_ISLAM = 'isadanislam.org'
const ISA_DAN_ALQURAN = 'isadanalquran.com'
const ISA_DAN_ALFATIHAH = 'isadanalfatihah.com'
const KAUM_WANITA = 'isaislamdankaumwanita.com'
const TAKUT_NERAKA = 'takutneraka.com'

export const scenarios: DemoScenario[] = [
  {
    label: 'Jawaban tersusun',
    question: 'Siapakah Isa Al-Masih menurut Kitab Suci?',
    answerSource: 'generated',
    answerText:
      'Kitab Suci memperkenalkan Isa Al-Masih sebagai Firman Allah yang menjadi manusia. Ia disebut telah ada sejak semula bersama Allah, lalu hadir di tengah manusia untuk menyatakan kasih dan kebenaran-Nya.\n\nDalam Injil, Isa Al-Masih berkata bahwa Ia datang bukan untuk menghakimi dunia, melainkan supaya dunia diselamatkan melalui Dia. Karena itu Ia dikenal bukan hanya sebagai nabi yang mengajar, tetapi sebagai jalan yang membawa manusia kembali kepada Allah.\n\nBagi banyak orang, yang paling menyentuh bukanlah mukjizat-Nya, melainkan kesediaan-Nya menerima orang yang merasa jauh dan tidak layak. Anda dipersilakan menelusuri sendiri bacaan di bawah ini.',
    citations: [
      {
        title: 'Siapakah Isa Al-Masih dalam Injil?',
        url: `https://${ISA_DAN_ISLAM}/siapakah-isa-al-masih/`,
        site: ISA_DAN_ISLAM,
      },
      {
        title: 'Firman yang Menjadi Manusia',
        url: `https://${ISA_DAN_ALQURAN}/firman-yang-menjadi-manusia/`,
        site: ISA_DAN_ALQURAN,
      },
    ],
  },
  {
    label: 'Jawaban kurasi',
    question: 'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
    answerSource: 'curated',
    answerText:
      'Kitab Suci berbicara tentang pengampunan yang tidak diukur dari seberapa sering seseorang jatuh. Ketika ditanya berapa kali seseorang harus mengampuni, Isa Al-Masih menjawab dengan angka yang jauh melampaui hitungan — maksudnya, pengampunan tidak dibatasi jumlah.\n\nDikatakan pula bahwa jika kita mengakui dosa kita, Allah setia dan adil untuk mengampuni serta membersihkan kita. Yang diminta bukan kesempurnaan lebih dahulu, melainkan kejujuran.\n\nBanyak orang merasa dosa yang berulang membuat mereka kehilangan hak untuk kembali. Bacaan berikut menjawab kekhawatiran itu secara langsung.',
    citations: [
      {
        title: 'Pengampunan yang Tidak Terbatas',
        url: `https://${ISA_DAN_ALFATIHAH}/pengampunan-yang-tidak-terbatas/`,
        site: ISA_DAN_ALFATIHAH,
      },
    ],
  },
  {
    label: 'Di luar cakupan',
    question: 'Tolong buatkan saya kode Python untuk mengurutkan daftar.',
    answerSource: 'refusal',
    citations: [],
  },
  {
    label: 'Tanpa dasar',
    question: 'Bagaimana pandangan Kitab Suci tentang penambangan aset kripto?',
    answerSource: 'no_grounding',
    citations: [],
  },
  {
    label: 'Tanggapan kepedulian',
    question: 'Saya merasa tidak sanggup lagi menjalani hidup ini.',
    answerSource: 'crisis',
    citations: [],
  },
  {
    label: 'Gangguan',
    question: 'Apa arti kasih karunia?',
    answerSource: 'error',
    citations: [],
  },
  {
    label: 'Batas pertanyaan',
    question: 'Apakah surga itu nyata?',
    answerSource: 'error',
    retryAfterSeconds: 20 * 60,
    citations: [],
  },
  {
    label: 'Pertanyaan perempuan',
    question: 'Bagaimana Isa Al-Masih memperlakukan perempuan?',
    answerSource: 'generated',
    answerText:
      'Catatan Injil menunjukkan sikap yang tidak lazim pada zamannya. Isa Al-Masih berbicara langsung dengan perempuan di ruang publik, menerima mereka sebagai murid yang belajar, dan membela mereka yang hendak dihukum orang banyak.\n\nKetika seorang perempuan dipermalukan di hadapan umum, Ia tidak ikut menghakimi, melainkan menantang para penuduhnya untuk memeriksa diri sendiri lebih dahulu. Kepada perempuan itu Ia berkata bahwa Ia pun tidak menghukumnya.\n\nBagi banyak pembaca perempuan, bagian inilah yang paling mengejutkan: martabat mereka tidak perlu diperjuangkan, sebab sudah lebih dahulu diakui.',
    citations: [
      {
        title: 'Perempuan dalam Pandangan Isa Al-Masih',
        url: `https://${KAUM_WANITA}/perempuan-dalam-pandangan-isa/`,
        site: KAUM_WANITA,
      },
      {
        title: 'Ia Tidak Menghukum',
        url: `https://${TAKUT_NERAKA}/ia-tidak-menghukum/`,
        site: TAKUT_NERAKA,
      },
    ],
  },
]

/** The scenario served when a question does not match any other. */
export const defaultScenario = scenarios[0]!

/** Naive keyword routing — good enough to make the demo feel responsive. */
export function pickScenario(question: string): DemoScenario {
  const q = question.toLowerCase()

  if (/(bunuh diri|mengakhiri hidup|tidak sanggup|ingin mati|putus asa)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'crisis')!
  }
  if (/(kode|python|javascript|resep|cuaca|sepak bola)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'refusal')!
  }
  if (/(kripto|bitcoin|saham|investasi)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'no_grounding')!
  }
  if (/(perempuan|wanita|istri)/.test(q)) {
    return scenarios.find((s) => s.label === 'Pertanyaan perempuan')!
  }
  if (/(ampun|dosa|bertobat)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'curated')!
  }
  return defaultScenario
}
