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

// 生成锚点id（简易slug）
function slugify(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

// 为h2/h3注入id并生成目录HTML
function injectToc(html) {
  try {
    const headingReg = /<h([23])>(.*?)<\/h\1>/g
    const headings = []
    let m
    let processed = html
    while ((m = headingReg.exec(html)) !== null) {
      const level = Number(m[1])
      const text = m[2].replace(/<[^>]+>/g, '')
      const id = slugify(text)
      headings.push({ level, text, id })
      processed = processed.replace(m[0], `<h${level} id="${id}">${m[2]}</h${level}>`)
    }
    if (headings.length < 2) return processed
    const tocItems = headings
      .map(h => `<li class="toc-li level-${h.level}"><a href="#${h.id}">${h.text}</a></li>`) 
      .join('')
    const tocHtml = `
      <nav class="toc-float">
        <div class="toc-title">目录</div>
        <ul class="toc-list">${tocItems}</ul>
      </nav>
    `
    return tocHtml + processed
  } catch (e) {
    console.warn('TOC inject failed:', e)
    return html
  }
}

// 包装代码块并添加复制按钮/语言标识
function enhanceCodeBlocks(html) {
  try {
    return html.replace(/<pre><code class=\"language-([^"]+)\">([\s\S]*?)<\/code><\/pre>/g, (_m, lang, code) => {
      const l = String(lang).toLowerCase()
      if (l === 'mermaid') {
        // 交给 Mermaid 渲染器处理
        return `<div class="mermaid">${code}</div>`
      }
      // 去掉代码块首尾的纯空行，保留内部换行
      const trimmed = String(code)
        .replace(/^(?:\s*\n)+/, '')     // 移除前导空白行
        .replace(/(?:\n\s*)+$/, '\n')  // 结尾最多保留一个换行
      return `
      <div class="code-block">
        <div class="code-toolbar">
          <span class="lang">${lang}</span>
          <button class="copy-btn" type="button">复制</button>
        </div>
        <pre><code class="language-${lang}">${trimmed}</code></pre>
      </div>`
    })
  } catch (e) {
    console.warn('Enhance code blocks failed:', e)
    return html
  }
}

// 折叠多余 <br> 或空段落（更保守的清理）
function collapseEmptyLines(html) {
  // 移除纯空段落（包含 &nbsp;）
  html = html.replace(/<p>\s*(?:&nbsp;\s*)?<\/p>/g, '')
  // 折叠连续3个以上的 <br> 为 2 个（保留基本段落呼吸）
  html = html.replace(/(<br\s*\/?>(\s|&nbsp;)*){3,}/g, '<br><br>')
  // 折叠重复的空段落组
  html = html.replace(/(<p>\s*<\/p>\s*){2,}/g, '')
  return html
}

// 预处理文本，清理多余空行
function preprocessText(text) {
  if (!text || typeof text !== 'string') return ''
  
  // -2.8) 规范化所有代码围栏，使 ``` 始终独立成行，避免“``` 不换行”导致的大段误包裹
  // 2.8.a) 若同一行在内容中间出现 ```（开/关围栏），在其前插入换行
  text = text.replace(/([^\n])```/g, '$1\n```')
  // 2.8.b) 若围栏开头后紧跟语言标识或其它内容（如 ```yaml something 或 ```---），在语言标识后强制换行
  text = text.replace(/(^|\n)([ \t]*```[ \t]*[a-zA-Z0-9_-]*)(\S)/g, '$1$2\n$3')

  // -2) 将本行行尾的 ``` 归并到下一行，规范为“独立一行的围栏关闭”
  // 例如：pods: "213"```  ->  pods: "213"\n```
  // 支持 >=3 个反引号的收尾归并
  text = text.replace(/^(?!\s*`{3,})([^\n]*?)`{3,}[ \t]*$/gm, (_m, before) => {
    const left = String(before).replace(/[ \t]+$/, '')
    return left + '\n```'
  })

  // -2.5) 若处于代码围栏内部，修复行尾仅含 1 或 2 个反引号的“误关围栏”
  // 现象：LLM/分片有时输出如 “466天``” 或 “...`” 试图结束代码块，导致后续整体被包裹
  // 策略：在围栏内遇到行尾 ` 或 `` 时，将其改为“本行结尾去掉这些反引号，下一行补上独立的 ``` 作为正确闭合”
  try {
    const lines = text.split(/\r?\n/)
    let inFence = false
    const fixed = []
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i]
      // 开/关 围栏识别（独立或带语言标记的开头）
      if (/^\s*```/.test(line)) {
        // 判断是开还是关：简单切换状态
        inFence = !inFence
        fixed.push(line)
        continue
      }
      if (inFence && /`{1,2}\s*$/.test(line) && !/`{3,}\s*$/.test(line)) {
        // 去掉尾部 1/2 个反引号，下一行补标准闭合围栏
        line = line.replace(/`{1,2}\s*$/, '')
        fixed.push(line)
        fixed.push('```')
        inFence = false
        continue
      }
      fixed.push(line)
    }
    text = fixed.join('\n')
  } catch (e) {
    // 忽略守护性修复中的异常
  }

  // -1) 若整篇以 ```text/plain/txt 围栏包裹，直接整体解包
  text = text.replace(/^\s*```(?:text|plain|txt)?[^\n]*\r?\n([\s\S]*?)\r?\n?```\s*$/,
    (_m, body) => String(body).replace(/^\s*\r?\n+/, '').replace(/\r?\n+\s*$/, '\n')
  )

  // 0) 围栏语法容错：修复常见的错误写法，避免被错误识别为代码块或无法闭合
  // ``yaml / ``bash -> ```yaml / ```bash
  text = text.replace(/(^|\n)\s*``\s*([a-zA-Z0-9_-]+)\s*\n/g, '$1```$2\n')
  // ``` yaml -> ```yaml（去除多余空格）
  text = text.replace(/(^|\n)\s*```\s+([a-zA-Z0-9_-]+)\s*\n/g, '$1```$2\n')
  // ```yaml1 / ```bash1 等：去掉尾部数字（列表序号粘连等）
  text = text.replace(/(^|\n)\s*```([a-zA-Z_-]+)\d+\s*\n/g, '$1```$2\n')
  
  // 清理多余的空行（保留最多一个连续空行）
  text = text.replace(/\n\s*\n\s*\n+/g, '\n\n')
  // 折叠 3 个以上的连续换行为 2 个
  text = text.replace(/\n{3,}/g, '\n\n')

  // 1) 将 ```markdown / ```md 围栏解包为普通文本，避免表格被当作代码块
  // 说明：以下所有围栏正则均要求“关闭围栏”必须出现在独立一行，以避免行内 ``` 误触发
  text = text.replace(/```(?:markdown|md)[^\n]*\r?\n([\s\S]*?)\r?\n?^[ \t]*```[ \t]*$/gm, (_m, body) => {
    const inner = String(body)
      .replace(/^\s*\r?\n+/, '')
      .replace(/\r?\n+\s*$/, '\n')
    return inner
  })

  // 1.5) 启发式解包：语言为空/text/plain/txt 且主体更像 Markdown（标题/列表/表格/引用）
  text = text.replace(/```([a-zA-Z0-9_-]*)[^\n]*\r?\n([\s\S]*?)\r?\n?^[ \t]*```[ \t]*$/gm, (m, lang, body) => {
    const l = String(lang || '').toLowerCase()
    const looksMarkdown = /(^|\n)\s*(#{1,6}\s|[-*+]\s|\d+\.\s|\|.*\||>\s)/.test(body)
    const lineCount = String(body).trim().split(/\r?\n/).length
    const isShortPlain = (l === 'text' || l === 'plain' || l === 'txt' || l === 'plaintext') && lineCount <= 2 && !/[{};()<>]/.test(body)
    const looksTeX = /\\\(|\\\)|\\\[|\\\]|\$\$|\\begin\{[\s\S]*?\}/.test(body)
    const shouldUnwrap = (
      (!l || l === 'text' || l === 'plain' || l === 'txt' || l === 'plaintext') && (looksMarkdown || isShortPlain)
    ) || (l === 'math' && !looksTeX)
    if (shouldUnwrap) {
      return String(body)
        .replace(/^\s*\r?\n+/, '')
        .replace(/\r?\n+\s*$/, '\n')
    }
    return m
  })

  // 2) 裁剪所有代码围栏首尾空行（yaml/bash/promql等），兼容CRLF
  text = text.replace(/```([a-zA-Z0-9_-]*)[^\n]*\r?\n([\s\S]*?)\r?\n?^[ \t]*```[ \t]*$/gm, (m, lang, body) => {
    const trimmedBody = String(body)
      .replace(/^\s*\r?\n+/, '')
      .replace(/\r?\n+\s*$/, '\n')
    return '```' + lang + '\n' + trimmedBody + '```'
  })
  
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
    // 原样渲染：不进行任何预处理与修复，仅做代码块与表格样式增强
    let html = marked.parse(text)
    html = enhanceCodeBlocks(html)
    html = enhanceClusterStatsHTML(html)
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
    // 原样渲染（流式）：不做补齐/不改行，仅做代码块与表格样式增强
    let html = marked.parse(text)
    html = enhanceCodeBlocks(html)
    html = enhanceClusterStatsHTML(html)
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
  
  // 轻量边框样式，避免过重的视觉噪音
  html = html.replace(
    /<table>/g,
    '<table style="border-collapse: separate !important; border-spacing: 0 !important; border: 1px solid #e4e7ed !important; width: 100%; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">'
  )
  
  // 强制表头和单元格边框
  html = html.replace(
    /<th>/g,
    '<th style="border-right: 1px solid #e9edf3 !important; border-bottom: 1px solid #e9edf3 !important; padding: 10px 12px; text-align: center; background: #f7f9fc; color: #303133; font-weight: 600;">'
  )
  
  html = html.replace(
    /<td>/g,
    '<td style="border-right: 1px solid #e9edf3 !important; border-bottom: 1px solid #e9edf3 !important; padding: 10px 12px; text-align: center; background: #fff;">'
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
    '<td style="$1 font-weight: 600; color: #2c7be5; font-size: 14px; background: #f6fbff;">$2</td>'
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
  // 统一按Markdown直接渲染（不做任何预处理），仅保留表格与代码块样式增强
  return isStreaming ? renderStreamingMarkdown(content) : renderMarkdown(content)
} 