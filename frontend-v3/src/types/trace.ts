export type TraceTone = 'blue' | 'pink' | 'green' | 'amber' | 'slate'

export interface TraceStep {
  id: string
  title: string
  meta: string
  detail: string
  icon: string
  tone: TraceTone
  badge?: string
  status?: string
  duration?: string
  metric?: string
}

export interface TraceChip {
  label: string
  value: string
  dark?: boolean
}

export interface TraceScore {
  label: string
  value: string
  detail: string
  tone: TraceTone
}

export type TraceTab = 'preview' | 'scores'
export type TraceFormat = 'formatted' | 'json'
