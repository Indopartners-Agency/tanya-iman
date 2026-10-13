import { describe, expect, it } from 'vitest'
import { backAction, type BackContext } from '../utils/backAction'

const base: BackContext = {
  path: '/chat',
  canGoBack: true,
  hasConversation: false,
  dialogOpen: false,
}

describe('backAction (Chat UX section 12)', () => {
  it('closes the exit dialog first if it is open', () => {
    expect(backAction({ ...base, hasConversation: true, dialogOpen: true })).toBe('close-dialog')
  })

  it('asks before leaving a conversation the seeker has started', () => {
    expect(backAction({ ...base, hasConversation: true })).toBe('confirm-exit')
  })

  it('goes back from an empty chat when there is history', () => {
    expect(backAction(base)).toBe('go-back')
  })

  it('pops in-app navigation from secondary screens', () => {
    expect(backAction({ ...base, path: '/privasi' })).toBe('go-back')
    expect(backAction({ ...base, path: '/masuk' })).toBe('go-back')
  })

  it('exits from the welcome screen', () => {
    expect(backAction({ ...base, path: '/' })).toBe('exit')
  })

  it('exits when there is nothing to go back to', () => {
    expect(backAction({ ...base, path: '/privasi', canGoBack: false })).toBe('exit')
  })
})
