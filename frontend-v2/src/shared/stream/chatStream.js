export const DONE_EVENT = 'done'

export const parseChatStreamLine = (line) => {
  if (!line || !line.startsWith('data:')) {
    return null
  }

  let content = line.slice(5)
  if (content.startsWith(' ')) {
    content = content.slice(1)
  }

  if (content.trim() === '[DONE]') {
    return { type: DONE_EVENT }
  }

  if (content.includes('__UPDATE_CONTENT__:') && content.includes('__END_UPDATE__')) {
    return {
      type: 'legacy_content_update',
      rawContent: content
    }
  }

  try {
    const parsed = JSON.parse(content)
    return normalizeChatStreamEvent(parsed)
  } catch (error) {
    return {
      type: 'message_delta',
      content
    }
  }
}

export const normalizeChatStreamEvent = (event) => {
  if (!event || typeof event !== 'object') {
    return {
      type: 'message_delta',
      content: String(event ?? '')
    }
  }

  if (event.type === 'tool_call_start') {
    const toolCall = event.tool_call || {}
    return {
      ...event,
      id: event.id || toolCall.id,
      tool: event.tool || toolCall.name,
      arguments: event.arguments || parseToolArguments(toolCall.arguments)
    }
  }

  if (event.type === 'tool_call_result' || event.type === 'tool_call_update') {
    const toolCall = event.tool_call || {}
    const success = typeof event.success === 'boolean'
      ? event.success
      : toolCall.status !== 'error' && !event.error

    return {
      ...event,
      type: 'tool_call_result',
      id: event.id || toolCall.id,
      tool: event.tool || toolCall.name,
      success,
      status: success ? 'success' : 'error',
      duration: event.duration || toolCall.duration || null
    }
  }

  if (event.type) {
    return event
  }

  if (Object.prototype.hasOwnProperty.call(event, 'content')) {
    return {
      type: 'message_delta',
      content: event.content || ''
    }
  }

  return {
    type: 'message_delta',
    content: JSON.stringify(event)
  }
}

export const createChatStreamParser = (onEvent) => {
  let buffer = ''

  const consume = async (text, flush = false) => {
    buffer += text
    const lines = buffer.split(/\r?\n/)
    buffer = flush ? '' : (lines.pop() || '')

    const completeLines = flush ? lines.concat(buffer ? [buffer] : []) : lines
    for (const line of completeLines) {
      if (!line) {
        continue
      }
      const event = parseChatStreamLine(line)
      if (event) {
        await onEvent(event)
      }
    }
  }

  return {
    push: (text) => consume(text, false),
    flush: () => consume('', true)
  }
}

const parseToolArguments = (rawArguments) => {
  if (!rawArguments) {
    return {}
  }
  if (typeof rawArguments === 'object') {
    return rawArguments
  }
  try {
    const parsed = JSON.parse(rawArguments)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed
      : { value: parsed }
  } catch (error) {
    return { raw: rawArguments }
  }
}
