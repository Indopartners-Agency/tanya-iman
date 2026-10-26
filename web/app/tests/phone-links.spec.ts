import { describe, expect, it } from 'vitest'
import { parseTextWithPhoneLinks } from '../utils/phoneLinks'

describe('parseTextWithPhoneLinks (F-30 & F-44 tappable phone links)', () => {
  it('extracts emergency short number 119 and landline (021) 500-454 in crisis copy', () => {
    const crisisText =
      'Jika Anda berada dalam kondisi darurat, segera hubungi 119 atau layanan kesehatan jiwa (021) 500-454 sekarang juga.'
    const parts = parseTextWithPhoneLinks(crisisText)
    const telParts = parts.filter((p) => p.tel)

    expect(telParts).toEqual([
      { text: '119', tel: '119' },
      { text: '(021) 500-454', tel: '021500454' },
    ])
  })

  it('extracts international Indonesian phone numbers in emotional deferral copy', () => {
    const emotionalText =
      'Jika Anda ingin berbicara dengan seseorang, silakan hubungi Tim Peduli: +62 812-3456-7890.'
    const parts = parseTextWithPhoneLinks(emotionalText)
    const telParts = parts.filter((p) => p.tel)

    expect(telParts).toEqual([{ text: '+62 812-3456-7890', tel: '+6281234567890' }])
  })

  it('returns a single plain text part when no phone numbers are present', () => {
    const plain = 'Selamat datang. Silakan tanyakan apa pun tentang iman.'
    expect(parseTextWithPhoneLinks(plain)).toEqual([{ text: plain }])
  })
})
