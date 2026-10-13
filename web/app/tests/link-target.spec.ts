import { describe, expect, it } from 'vitest'
import { citationLinkMode } from '../utils/linkTarget'

describe('citationLinkMode (Chat UX sections 9 and 11)', () => {
  it('opens a new tab on web', () => {
    expect(citationLinkMode('web')).toBe('new-tab')
  })

  it('escapes the iframe in the widget', () => {
    expect(citationLinkMode('widget')).toBe('top')
  })

  it('hands the link to the system browser on Android, never the WebView', () => {
    expect(citationLinkMode('android')).toBe('system')
  })
})
