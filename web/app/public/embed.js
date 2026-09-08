/**
 * Tanya Iman embed loader (F-27).
 *
 * A WordPress site owner drops one script tag on their page:
 *
 *   <script src="https://app.tanyaiman.id/embed.js" defer></script>
 *
 * Everything the widget does happens inside an iframe. Nothing here reads or
 * writes the host page beyond appending its own nodes, and no host-page data
 * ever reaches our origin — which is what lets a site owner add this without a
 * security review.
 *
 * The backend must list the host origin in FRAME_ANCESTORS before the iframe
 * will render; see the CSP middleware in backend/main.py.
 */
;(function () {
  'use strict'

  if (window.__tanyaImanEmbedLoaded) return
  window.__tanyaImanEmbedLoaded = true

  var script = document.currentScript
  var origin = new URL(script.src).origin
  var config = {
    label: script.getAttribute('data-label') || 'Tanya Iman',
    position: script.getAttribute('data-position') || 'right',
  }

  var side = config.position === 'left' ? 'left' : 'right'
  var open = false

  var launcher = document.createElement('button')
  launcher.type = 'button'
  launcher.setAttribute('aria-label', config.label)
  launcher.setAttribute('aria-expanded', 'false')
  launcher.textContent = config.label
  launcher.style.cssText = [
    'position:fixed',
    'bottom:20px',
    side + ':20px',
    'z-index:2147483000',
    'padding:12px 20px',
    'border:0',
    'border-radius:9999px',
    'background:#0f3d2e',
    'color:#fff',
    'font:500 15px/1 ui-sans-serif,system-ui,sans-serif',
    'box-shadow:0 4px 14px rgba(0,0,0,.18)',
    'cursor:pointer',
  ].join(';')

  var frame = document.createElement('iframe')
  frame.title = config.label
  frame.src = origin + '/#/chat?embed=1'
  frame.setAttribute('allow', 'clipboard-write')
  // No allow-same-origin: the widget has no business touching the host page's
  // storage or DOM, and withholding it makes that structural.
  frame.setAttribute('sandbox', 'allow-scripts allow-forms allow-popups')
  frame.style.cssText = [
    'position:fixed',
    'bottom:84px',
    side + ':20px',
    'z-index:2147483000',
    'width:min(400px,calc(100vw - 40px))',
    'height:min(620px,calc(100vh - 120px))',
    'border:0',
    'border-radius:16px',
    'box-shadow:0 12px 40px rgba(0,0,0,.22)',
    'background:#f8fafc',
    'display:none',
  ].join(';')

  function toggle() {
    open = !open
    frame.style.display = open ? 'block' : 'none'
    launcher.setAttribute('aria-expanded', String(open))
  }

  launcher.addEventListener('click', toggle)

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && open) toggle()
  })

  // The widget reports its content height so a long answer is not clipped and
  // a short one does not leave a band of empty space (Chat UX section 11).
  var MAX_HEIGHT_PX = 620

  window.addEventListener('message', function (event) {
    if (event.source !== frame.contentWindow) return
    if (!event.data || event.data.type !== 'tanya-iman:height') return

    var next = Number(event.data.height)
    if (!isFinite(next) || next <= 0) return

    frame.style.height =
      'min(' + Math.min(next, MAX_HEIGHT_PX) + 'px, calc(100vh - 120px))'
  })

  function mount() {
    document.body.appendChild(frame)
    document.body.appendChild(launcher)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount)
  } else {
    mount()
  }
})()
