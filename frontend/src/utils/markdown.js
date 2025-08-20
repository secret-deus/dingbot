import { marked } from 'marked'
import hljs from 'highlight.js'

// 配置marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.warn('Highlight error:', err)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: false,
  gfm: true
})

// 折叠多余 <br> 或空段落（更保守的清理）
function collapseEmptyLines(html) {
  // 只移除完全空的段落
  html = html.replace(/<p>\s*<\/p>/g, '')
  
  // 只移除过多的连续 <br> 标签（保留最多两个）
  html = html.replace(/(<br\s*\/?>\s*){3,}/g, '<br><br>')
  
  return html
}

// 预处理文本，清理多余空行
function preprocessText(text) {
  if (!text || typeof text !== 'string') return ''
  
  // 清理多余的空行（保留最多一个连续空行）
  text = text.replace(/\n\s*\n\s*\n+/g, '\n\n')
  
  // 清理行尾空白（但保留换行符）
  text = text.replace(/[ \t]+$/gm, '')
  
  // 只清理开头和结尾的多余空行，但保留必要的换行
  text = text.replace(/^\n+/, '').replace(/\n+$/, '')
  
  return text
}

// 检测是否包含markdown语法
export function containsMarkdown(text) {
  if (!text || typeof text !== 'string') return false
  
  const markdownPatterns = [
    /```[\s\S]*?```/,        // 代码块
    /`[^`]+`/,               // 行内代码
    /^\s*#{1,6}\s+/m,        // 标题
    /^\s*[-*+]\s+/m,         // 列表
    /^\s*\d+\.\s+/m,         // 有序列表
    /\*\*[^*]+\*\*/,         // 粗体
    /\*[^*]+\*/,             // 斜体
    /\[[^\]]*\]\([^)]*\)/,   // 链接
    /^\s*>\s+/m,             // 引用
    /^\s*\|.*\|/m,           // 表格
    /---+/,                  // 分割线
  ]
  
  return markdownPatterns.some(pattern => pattern.test(text))
}

// 渲染完整markdown
export function renderMarkdown(text) {
  if (!text || typeof text !== 'string') return ''
  
  try {
    // 预处理文本
    text = preprocessText(text)
    
    // 将双反斜杠的分隔符还原为单反斜杠，避免 \( ... \) 无法识别
    text = text
      .replace(/\\\\\(/g, '\\(')
      .replace(/\\\\\)/g, '\\)')
      .replace(/\\\\\[/g, '\\[')
      .replace(/\\\\\]/g, '\\]')
    const html = collapseEmptyLines(marked.parse(text))
    return `<div class="markdown-content">${html}</div>`
  } catch (error) {
    console.error('Markdown render error:', error)
    return `<div class="markdown-content">${escapeHtml(text)}</div>`
  }
}

// 流式markdown渲染（处理不完整的markdown）
export function renderStreamingMarkdown(text) {
  if (!text || typeof text !== 'string') return ''
  
  try {
    // 预处理文本（流式渲染时稍微保守一些）
    text = preprocessText(text)
    
    text = text
      .replace(/\\\\\(/g, '\\(')
      .replace(/\\\\\)/g, '\\)')
      .replace(/\\\\\[/g, '\\[')
      .replace(/\\\\\]/g, '\\]')
    // 对于流式内容，先尝试修复不完整的代码块
    let processedText = text
    
    // 修复不完整的代码块
    const codeBlockMatches = text.match(/```[^`]*$/m)
    if (codeBlockMatches) {
      processedText = text + '\n```'
    }
    
    const html = collapseEmptyLines(marked.parse(processedText))
    return `<div class="markdown-content">${html}</div>`
  } catch (error) {
    console.error('Streaming markdown render error:', error)
    return `<div class="markdown-content">${escapeHtml(text)}</div>`
  }
}

// HTML转义
function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 增强HTML处理，为集群统计数据添加样式类
function enhanceClusterStatsHTML(html) {
  // 为统计数据段落添加样式类
  html = html.replace(
    /<p>(.*?(总资源数量|总关系数量|命名空间数量|异常资源数量).*?)<\/p>/g,
    '<p class="stats-item">$1</p>'
  )
  
  // 强制表格边框样式 - 使用内联样式确保显示
  html = html.replace(
    /<table>/g,
    '<table style="border-collapse: separate !important; border-spacing: 0 !important; border: 1px solid #666666 !important; width: 100%; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">'
  )
  
  // 强制表头和单元格边框
  html = html.replace(
    /<th>/g,
    '<th style="border: 1px solid #666666 !important; padding: 12px 15px; text-align: center; background: linear-gradient(135deg, #409EFF, #36a3f7); color: white; font-weight: 600;">'
  )
  
  html = html.replace(
    /<td>/g,
    '<td style="border: 1px solid #666666 !important; padding: 12px 15px; text-align: center; background: #fff;">'
  )
  
  // 为表格中的0值添加样式类
  html = html.replace(
    /<td style="([^"]*)">\s*0\s*<\/td>/g,
    '<td style="$1 color: #909399; font-style: italic;">0</td>'
  )
  
  // 为表格中的占位符添加样式类
  html = html.replace(
    /<td style="([^"]*)">\s*-\s*<\/td>/g,
    '<td style="$1 color: #c0c4cc; font-weight: normal;">-</td>'
  )
  
  // 为表格中的数字列添加居中对齐和样式
  html = html.replace(
    /<td style="([^"]*)">\s*(\d+)\s*<\/td>/g,
    '<td style="$1 font-weight: 700; color: #409EFF; font-size: 15px; background: #f0f9ff;">$2</td>'
  )
  
  // 为第一列（资源名称）左对齐
  html = html.replace(
    /<tr>\s*<td style="([^"]*)">(.*?)<\/td>/g,
    '<tr><td style="$1 text-align: left !important; font-weight: 600;">$2</td>'
  )
  
  // 为Pod状态等关键指标添加颜色
  html = html.replace(
    /<td style="([^"]*)">(Running|Pending|Failed|Unknown|CrashLoopBackOff|Terminating)<\/td>/g,
    (match, style, status) => {
      const colors = {
        'Running': '#67c23a',
        'Pending': '#e6a23c', 
        'Failed': '#f56c6c',
        'Unknown': '#909399',
        'CrashLoopBackOff': '#f56c6c',
        'Terminating': '#e6a23c'
      }
      const color = colors[status] || '#909399'
      return `<td style="${style} color: ${color}; font-weight: 600;">${status}</td>`
    }
  )
  
  return html
}

// 格式化消息内容
export function formatMessageContent(content, isStreaming = false) {
  if (!content || typeof content !== 'string') return ''
  
  // 调试：打印内容和检测结果
  const hasMarkdown = containsMarkdown(content)
  console.log('格式化内容:', { 
    length: content.length, 
    hasMarkdown, 
    preview: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
    newlineCount: (content.match(/\n/g) || []).length
  })
  
  // 检测是否包含markdown语法
  if (hasMarkdown) {
    let result = isStreaming ? renderStreamingMarkdown(content) : renderMarkdown(content)
    
    // 如果内容看起来是集群统计数据，应用增强样式
    if (content.includes('总资源数量') || content.includes('命名空间分布') || content.includes('Pod状态')) {
      result = enhanceClusterStatsHTML(result)
    }
    
    console.log('Markdown渲染结果预览:', result.substring(0, 200) + '...')
    return result
  }
  
  // 普通文本处理 - 保留换行符和格式
  const result = `<div class="text-content">${escapeHtml(content).replace(/\n/g, '<br>')}</div>`
  console.log('普通文本渲染结果预览:', result.substring(0, 200) + '...')
  return result
} 