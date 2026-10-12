/**
 * embed.spec.ts — Phase 7 Task 7.1
 *
 * Unit tests for the embed.js loader contract:
 *   - data-attribute configuration (label, position)
 *   - Idempotency guard (window.__tanyaImanEmbedLoaded)
 *   - postMessage height resize listener
 *   - Escape key closes the panel
 *   - iframe sandbox attributes
 *   - iframe src construction
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// ─── Minimal DOM environment helpers ────────────────────────────────────────

function makeScriptTag(src: string, attrs: Record<string, string> = {}): HTMLScriptElement {
  const el = document.createElement('script')
  el.src = src
  for (const [k, v] of Object.entries(attrs)) {
    el.setAttribute(k, v)
  }
  return el
}

/**
 * Load embed.js in the current JSDOM window by evaluating it as a string.
 * We read the file content and eval it so we can control document.currentScript.
 */
async function loadEmbed(scriptAttrs: Record<string, string> = {}) {
  // Reset the guard so each test gets a fresh load
  delete (window as any).__tanyaImanEmbedLoaded

  const fs = await import('fs')
  const path = await import('path')
  const embedPath = path.resolve(__dirname, '../../app/public/embed.js')
  let src = fs.readFileSync(embedPath, 'utf-8')

  // Stub document.currentScript to return a synthetic script element
  const scriptEl = makeScriptTag('https://app.tanyaiman.id/embed.js', scriptAttrs)
  Object.defineProperty(document, 'currentScript', {
    get: () => scriptEl,
    configurable: true,
  })

  // Ensure body exists
  if (!document.body) {
    document.body = document.createElement('body')
  }

  // Execute the embed script
  // eslint-disable-next-line no-eval
  eval(src)

  // Give any DOMContentLoaded listeners a tick to fire
  await new Promise((r) => setTimeout(r, 0))
}

// ─── Cleanup between tests ───────────────────────────────────────────────────

afterEach(() => {
  // Remove all injected launcher buttons and iframes
  document.querySelectorAll('button[aria-label]').forEach((el) => el.remove())
  document.querySelectorAll('iframe[title]').forEach((el) => el.remove())
  delete (window as any).__tanyaImanEmbedLoaded
})

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('embed.js — Idempotency', () => {
  it('loads only once even when the script runs twice', async () => {
    await loadEmbed()
    const countBefore = document.querySelectorAll('button[aria-label]').length
    await loadEmbed() // second load — should be no-op
    const countAfter = document.querySelectorAll('button[aria-label]').length
    expect(countAfter).toBe(countBefore)
  })

  it('sets window.__tanyaImanEmbedLoaded = true on first load', async () => {
    await loadEmbed()
    expect((window as any).__tanyaImanEmbedLoaded).toBe(true)
  })
})

describe('embed.js — Launcher button', () => {
  it('appends a button to document.body', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]')
    expect(btn).not.toBeNull()
  })

  it('uses default label "Tanya Iman" when data-label is absent', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label="Tanya Iman"]')
    expect(btn).not.toBeNull()
    expect(btn?.textContent?.trim()).toBe('Tanya Iman')
  })

  it('uses custom label from data-label attribute', async () => {
    await loadEmbed({ 'data-label': 'Ada Pertanyaan?' })
    const btn = document.querySelector('button[aria-label="Ada Pertanyaan?"]')
    expect(btn).not.toBeNull()
  })

  it('sets aria-expanded="false" initially', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]')
    expect(btn?.getAttribute('aria-expanded')).toBe('false')
  })

  it('positions on the right by default', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]') as HTMLElement
    expect(btn?.style.cssText).toContain('right')
    expect(btn?.style.cssText).not.toContain('left:')
  })

  it('positions on the left when data-position="left"', async () => {
    await loadEmbed({ 'data-position': 'left' })
    const btn = document.querySelector('button[aria-label]') as HTMLElement
    expect(btn?.style.cssText).toContain('left')
  })
})

describe('embed.js — iframe', () => {
  it('appends an iframe to document.body', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe')
    expect(frame).not.toBeNull()
  })

  it('iframe src ends with /chat?embed=1', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    expect(frame.src).toMatch(/\/chat\?embed=1$/)
  })

  it('iframe is hidden initially', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    expect(frame.style.display).toBe('none')
  })

  it('iframe sandbox contains required permissions', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    const sandbox = frame.getAttribute('sandbox') || ''
    expect(sandbox).toContain('allow-scripts')
    expect(sandbox).toContain('allow-forms')
    expect(sandbox).toContain('allow-popups')
  })

  it('iframe sandbox does NOT contain allow-same-origin', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    const sandbox = frame.getAttribute('sandbox') || ''
    expect(sandbox).not.toContain('allow-same-origin')
  })
})

describe('embed.js — Toggle behaviour', () => {
  it('shows iframe when launcher button is clicked', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]') as HTMLButtonElement
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    btn.click()
    expect(frame.style.display).toBe('block')
    expect(btn.getAttribute('aria-expanded')).toBe('true')
  })

  it('hides iframe when launcher button is clicked again', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]') as HTMLButtonElement
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    btn.click() // open
    btn.click() // close
    expect(frame.style.display).toBe('none')
    expect(btn.getAttribute('aria-expanded')).toBe('false')
  })

  it('closes on Escape key when open', async () => {
    await loadEmbed()
    const btn = document.querySelector('button[aria-label]') as HTMLButtonElement
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    btn.click() // open
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(frame.style.display).toBe('none')
  })

  it('does not toggle on Escape when already closed', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(frame.style.display).toBe('none') // still hidden
  })
})

describe('embed.js — postMessage height resize', () => {
  it('resizes iframe height on valid tanya-iman:height message', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement

    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: 'tanya-iman:height', height: 400 },
        source: (frame as any).contentWindow ?? window,
      }),
    )

    expect(frame.style.height).toContain('400')
  })

  it('ignores height messages with invalid (negative) values', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    const before = frame.style.height

    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: 'tanya-iman:height', height: -100 },
        source: (frame as any).contentWindow ?? window,
      }),
    )

    expect(frame.style.height).toBe(before)
  })

  it('ignores unknown message types', async () => {
    await loadEmbed()
    const frame = document.querySelector('iframe') as HTMLIFrameElement
    const before = frame.style.height

    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: 'other-app:event', payload: 'x' },
        source: (frame as any).contentWindow ?? window,
      }),
    )

    expect(frame.style.height).toBe(before)
  })
})
