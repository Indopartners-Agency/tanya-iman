import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import idLocale from '../locales/id.json'
import { usePlatform } from '../composables/usePlatform'

describe('Welcome Screen (F-1 & F-4 Requirements)', () => {
  it('defines the three required authentication paths in Indonesian copy', () => {
    // F-1: SMS, WhatsApp, and Guest are all first-class sign-in options.
    expect(idLocale.ui.login_sms).toBe('Masuk dengan SMS')
    expect(idLocale.ui.login_whatsapp).toBe('Masuk dengan WhatsApp')
    expect(idLocale.ui.login_guest).toBe('Lanjut sebagai Tamu')

    // Must be non-empty and mutually distinct
    const options = [idLocale.ui.login_sms, idLocale.ui.login_whatsapp, idLocale.ui.login_guest]
    expect(new Set(options).size).toBe(3)
  })

  it('defines F-4 privacy policy link copy', () => {
    // F-4: Every screen must provide an accessible privacy policy link.
    expect(idLocale.ui.privacy).toBe('Kebijakan Privasi')
  })

  it('defines F-6 persistent source note copy', () => {
    // F-6: Persistent source note informing seeker of the scripture-grounded nature.
    expect(idLocale.shared.source_note).toBe('Jawaban disusun berdasarkan Kitab Suci.')
  })
})

describe('Platform Detection (F-24 & Embed Mode)', () => {
  const originalWindow = globalThis.window

  beforeEach(() => {
    vi.stubGlobal('window', {
      self: {},
      top: {},
      location: { protocol: 'https:' },
    })
  })

  afterEach(() => {
    if (originalWindow) {
      vi.stubGlobal('window', originalWindow)
    } else {
      vi.unstubAllGlobals()
    }
  })

  it('detects standard standalone web platform when self === top', () => {
    const win = globalThis.window as any
    win.self = win
    win.top = win

    const result = usePlatform()
    expect(result.platform).toBe('web')
    expect(result.embedOrigin).toBeNull()
  })

  it('detects embedded widget platform when self !== top', () => {
    const win = globalThis.window as any
    win.self = {}
    win.top = {}
    vi.stubGlobal('document', {
      referrer: 'https://isadanislam.org/artikel-keselamatan',
    })

    const result = usePlatform()
    expect(result.platform).toBe('widget')
    expect(result.embedOrigin).toBe('https://isadanislam.org')
  })

  it('detects android platform when Capacitor is present', () => {
    const win = globalThis.window as any
    win.Capacitor = {}

    const result = usePlatform()
    expect(result.platform).toBe('android')
    expect(result.embedOrigin).toBeNull()
  })
})
