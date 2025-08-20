export let katexLoaded = false

export async function loadKatex () {
  if (katexLoaded) return
  if (typeof window === 'undefined') return

  const cssHref = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css'
  const jsSrc = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js'
  const renderSrc = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js'

  function loadLink (href) {
    return new Promise((resolve) => {
      if (document.querySelector(`link[href="${href}"]`)) return resolve()
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = href
      link.onload = () => resolve()
      document.head.appendChild(link)
    })
  }

  function loadScript (src) {
    return new Promise((resolve) => {
      if (document.querySelector(`script[src="${src}"]`)) return resolve()
      const script = document.createElement('script')
      script.src = src
      script.defer = true
      script.onload = () => resolve()
      document.body.appendChild(script)
    })
  }

  await loadLink(cssHref)
  await loadScript(jsSrc)
  await loadScript(renderSrc)
  katexLoaded = true
} 