export const OPS_THEME_STORAGE_KEY = 'ding-robot.ops.theme'

export const OPS_THEMES = [
  {
    id: 'graphite',
    name: 'Graphite Amber'
  },
  {
    id: 'forest',
    name: 'Forest Terminal'
  },
  {
    id: 'mono',
    name: 'Mono Zinc'
  }
]

export const getSavedOpsTheme = () => {
  const saved = localStorage.getItem(OPS_THEME_STORAGE_KEY)
  return OPS_THEMES.some((theme) => theme.id === saved) ? saved : 'graphite'
}

export const applyOpsTheme = (themeId) => {
  const nextTheme = OPS_THEMES.some((theme) => theme.id === themeId) ? themeId : 'graphite'
  document.documentElement.dataset.opsTheme = nextTheme
  localStorage.setItem(OPS_THEME_STORAGE_KEY, nextTheme)
  return nextTheme
}

export const getThemeName = (themeId) => {
  return OPS_THEMES.find((theme) => theme.id === themeId)?.name || OPS_THEMES[0].name
}
