<template>
  <div class="chat-history">
    <div class="history-header-card">
      <div class="header-content">
        <div class="header-title">
          <h3>对话历史</h3>
          <el-tag size="small" type="info" effect="plain">{{ chatStore.sessionHistory.length }} 个会话</el-tag>
        </div>

        <div class="header-actions">
          <el-tooltip content="收起侧栏" placement="bottom">
            <el-button size="small" circle @click="emit('collapse')">
              <el-icon><Fold /></el-icon>
            </el-button>
          </el-tooltip>

          <el-tooltip content="新建对话" placement="bottom">
            <el-button type="primary" size="small" circle @click="createNewSession">
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>

          <el-dropdown @command="handleMenuCommand" placement="bottom-end">
            <el-button size="small" circle title="更多">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="exportAll">
                  <el-icon><Download /></el-icon>
                  导出全部历史
                </el-dropdown-item>
                <el-dropdown-item command="importHistory">
                  <el-icon><Upload /></el-icon>
                  导入历史记录
                </el-dropdown-item>
                <el-dropdown-item command="clearAll" divided>
                  <el-icon><Delete /></el-icon>
                  清空全部历史
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 搜索和过滤 - 卡片式布局 -->
    <div class="search-section-card">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索对话..."
          size="small"
          clearable
          @input="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-tooltip content="筛选" placement="bottom">
          <el-button
            size="small"
            circle
            @click="showFilters = !showFilters"
            :type="hasActiveFilters ? 'primary' : 'default'"
          >
            <el-icon><Filter /></el-icon>
          </el-button>
        </el-tooltip>
        <el-badge v-if="activeFilterCount > 0" :value="activeFilterCount" class="filter-badge" />
      </div>
    </div>

    <!-- 过滤器面板 -->
    <el-collapse-transition>
      <div v-if="showFilters" class="filters-panel">
        <div class="filter-row">
          <label>标签:</label>
          <el-select
            v-model="selectedTags"
            multiple
            placeholder="选择标签"
            size="small"
            style="width: 200px"
          >
            <el-option
              v-for="tag in chatStore.getAllTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </div>

        <div class="filter-row">
          <label>日期范围:</label>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            size="small"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </div>

        <div class="filter-row">
          <label>消息数量:</label>
          <el-input-number
            v-model="messageCountRange.min"
            :min="0"
            size="small"
            placeholder="最少"
            style="width: 80px"
          />
          <span style="margin: 0 8px">-</span>
          <el-input-number
            v-model="messageCountRange.max"
            :min="0"
            size="small"
            placeholder="最多"
            style="width: 80px"
          />
        </div>

        <div class="filter-actions">
          <el-button size="small" @click="clearFilters">清空筛选</el-button>
          <el-button size="small" type="primary" @click="applyFilters">应用筛选</el-button>
        </div>
      </div>
    </el-collapse-transition>

    <!-- 会话列表 -->
    <div class="sessions-list">
      <div v-if="filteredSessions.length === 0" class="empty-state">
        <el-empty description="没有找到符合条件的对话" />
      </div>

      <div
        v-for="session in filteredSessions"
        :key="session.id"
        :class="['session-card', { 'session-card-active': session.id === chatStore.currentSessionId }]"
        @click="switchToSession(session.id)"
      >
        <div class="session-main">
          <div class="session-title-container">
            <el-icon class="item-icon"><ChatDotRound /></el-icon>
            <div class="session-info">
              <div
                v-if="editingSessionId === session.id"
                class="title-edit"
              >
                <el-input
                  v-model="editingTitle"
                  size="small"
                  @blur="saveTitle(session.id)"
                  @keydown.enter="saveTitle(session.id)"
                  @keydown.esc="cancelEdit"
                  @click.stop
                  ref="titleInput"
                />
              </div>
              <div
                v-else
                class="session-title"
                @dblclick.stop="startEditTitle(session)"
              >
                {{ session.title }}
              </div>
              <div class="session-preview">
                {{ session.preview || '暂无摘要' }}
              </div>

              <div class="session-meta">
                <span>{{ session.metadata?.messageCount || 0 }} 条消息</span>
                <span class="last-activity">{{ formatTime(session.metadata?.lastActivity || session.updatedAt) }}</span>
              </div>
            </div>
          </div>

          <div class="session-actions" @click.stop>
            <el-dropdown @command="(cmd) => handleSessionCommand(cmd, session)" placement="bottom-end">
              <el-button link size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">
                    <el-icon><Edit /></el-icon>
                    重命名
                  </el-dropdown-item>
                  <el-dropdown-item command="export">
                    <el-icon><Download /></el-icon>
                    导出对话
                  </el-dropdown-item>
                  <el-dropdown-item command="duplicate">
                    <el-icon><CopyDocument /></el-icon>
                    复制对话
                  </el-dropdown-item>
                  <el-dropdown-item command="tags">
                    <el-icon><PriceTag /></el-icon>
                    管理标签
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    删除对话
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 标签显示 -->
        <div v-if="(session.metadata?.tags || []).length > 0" class="session-tags">
          <el-tag
            v-for="tag in session.metadata?.tags || []"
            :key="tag"
            size="small"
            type="info"
            effect="plain"
            class="session-tag"
          >
            {{ tag }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 标签管理对话框 -->
    <el-dialog
      v-model="tagDialogVisible"
      title="管理标签"
      width="400px"
    >
      <div class="tag-management">
        <div class="current-tags">
          <h4>当前标签:</h4>
          <div class="tags-container">
            <el-tag
              v-for="tag in currentSessionTags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <div class="add-tag">
          <h4>添加标签:</h4>
          <el-input
            v-model="newTag"
            placeholder="输入新标签"
            size="small"
            @keydown.enter="addTag"
            style="width: 200px"
          />
          <el-button size="small" type="primary" @click="addTag" :disabled="!newTag.trim()">
            添加
          </el-button>
        </div>

        <div class="suggested-tags">
          <h4>建议标签:</h4>
          <div class="tags-container">
            <el-tag
              v-for="tag in suggestedTags"
              :key="tag"
              type="info"
              class="suggested-tag"
              @click="addSuggestedTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 导入文件隐藏input -->
    <input
      ref="importFileInput"
      type="file"
      accept=".json"
      style="display: none"
      @change="handleImportFile"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, MoreFilled, Search, Filter, Download, Upload, Delete, Fold,
  Edit, CopyDocument, PriceTag, ChatDotRound
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['session-switched', 'collapse'])

// 响应式数据
const chatStore = useChatStore()
const searchQuery = ref('')
const showFilters = ref(false)
const selectedTags = ref([])
const dateRange = ref([])
const messageCountRange = ref({ min: null, max: null })
const filteredSessions = ref([])

// 编辑状态
const editingSessionId = ref(null)
const editingTitle = ref('')
const titleInput = ref(null)

// 标签管理
const tagDialogVisible = ref(false)
const currentSessionTags = ref([])
const newTag = ref('')
const managingSessionId = ref(null)
const importFileInput = ref(null)

// 计算属性
const hasActiveFilters = computed(() => {
  return selectedTags.value.length > 0 ||
         dateRange.value.length > 0 ||
         messageCountRange.value.min !== null ||
         messageCountRange.value.max !== null
})

const activeFilterCount = computed(() => {
  let count = 0
  if (selectedTags.value.length > 0) count++
  if (dateRange.value.length > 0) count++
  if (messageCountRange.value.min !== null || messageCountRange.value.max !== null) count++
  return count
})

const suggestedTags = computed(() => {
  const commonTags = ['工作', '学习', '测试', '重要', '问题', 'K8s', '运维', '部署']
  return commonTags.filter(tag => !currentSessionTags.value.includes(tag))
})

// 方法
const handleSearch = () => {
  applyFilters()
}

const applyFilters = () => {
  const options = {
    tags: selectedTags.value,
    dateRange: dateRange.value.length === 2 ? {
      start: new Date(dateRange.value[0]),
      end: new Date(dateRange.value[1])
    } : null,
    messageCountRange: {
      min: messageCountRange.value.min,
      max: messageCountRange.value.max
    }
  }

  filteredSessions.value = chatStore.searchSessions(searchQuery.value, options)
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
  dateRange.value = []
  messageCountRange.value = { min: null, max: null }
  applyFilters()
}

const createNewSession = () => {
  const session = chatStore.createSession()
  emit('session-switched', session.id)
  ElMessage.success('已创建新对话')
}

const switchToSession = (sessionId) => {
  chatStore.switchToSession(sessionId)
  emit('session-switched', sessionId)
}

const handleMenuCommand = (command) => {
  switch (command) {
    case 'exportAll':
      exportAllHistory()
      break
    case 'importHistory':
      importHistory()
      break
    case 'clearAll':
      clearAllHistory()
      break
  }
}

const handleSessionCommand = (command, session) => {
  switch (command) {
    case 'rename':
      startEditTitle(session)
      break
    case 'export':
      exportSession(session.id)
      break
    case 'duplicate':
      duplicateSession(session.id)
      break
    case 'tags':
      manageSessionTags(session.id)
      break
    case 'delete':
      deleteSession(session.id)
      break
  }
}

// 标题编辑
const startEditTitle = (session) => {
  editingSessionId.value = session.id
  editingTitle.value = session.title
  nextTick(() => {
    titleInput.value?.focus()
  })
}

const saveTitle = (sessionId) => {
  if (editingTitle.value.trim()) {
    chatStore.updateSessionTitle(sessionId, editingTitle.value.trim())
    ElMessage.success('标题已更新')
  }
  cancelEdit()
}

const cancelEdit = () => {
  editingSessionId.value = null
  editingTitle.value = ''
}

// 导入导出
const exportAllHistory = () => {
  try {
    const data = chatStore.exportAllSessions()
    const dataStr = JSON.stringify(data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })

    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `chat_history_all_${new Date().toISOString().slice(0, 10)}.json`
    link.click()

    URL.revokeObjectURL(link.href)
    ElMessage.success('历史记录已导出')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出历史记录失败')
  }
}

const exportSession = (sessionId) => {
  try {
    const data = chatStore.exportSession(sessionId)
    if (!data) {
      ElMessage.error('会话不存在')
      return
    }

    const dataStr = JSON.stringify(data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })

    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `chat_session_${sessionId.slice(-8)}_${new Date().toISOString().slice(0, 10)}.json`
    link.click()

    URL.revokeObjectURL(link.href)
    ElMessage.success('对话已导出')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出对话失败')
  }
}

const importHistory = () => {
  importFileInput.value?.click()
}

const handleImportFile = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)

      if (chatStore.importSessions(data)) {
        ElMessage.success('历史记录导入成功')
        applyFilters() // 刷新列表
      } else {
        ElMessage.error('无效的历史记录格式')
      }
    } catch (error) {
      console.error('导入失败:', error)
      ElMessage.error('导入历史记录失败')
    }
  }

  reader.readAsText(file)
  event.target.value = ''
}

const clearAllHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有历史记录吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    chatStore.clearAllSessions()
    ElMessage.success('历史记录已清空')
  } catch {
    // 用户取消
  }
}

const deleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个对话吗？此操作不可恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    chatStore.deleteSession(sessionId)
    ElMessage.success('对话已删除')
    applyFilters() // 刷新列表
  } catch {
    // 用户取消
  }
}

const duplicateSession = (sessionId) => {
  const originalSession = chatStore.sessions.get(sessionId)
  if (originalSession) {
    const newSession = chatStore.createSession(`${originalSession.title} (副本)`)
    newSession.messages = [...originalSession.messages]
    newSession.toolCalls = [...originalSession.toolCalls]
    newSession.metadata.tags = [...originalSession.metadata.tags]
    chatStore.saveToStorage()

    ElMessage.success('对话已复制')
    applyFilters() // 刷新列表
  }
}

// 标签管理
const manageSessionTags = (sessionId) => {
  managingSessionId.value = sessionId
  const session = chatStore.sessions.get(sessionId)
  if (session) {
    currentSessionTags.value = [...session.metadata.tags]
    tagDialogVisible.value = true
  }
}

const addTag = () => {
  const tag = newTag.value.trim()
  if (tag && !currentSessionTags.value.includes(tag)) {
    currentSessionTags.value.push(tag)
    chatStore.addSessionTag(managingSessionId.value, tag)
    newTag.value = ''
    ElMessage.success(`标签 "${tag}" 已添加`)
  }
}

const addSuggestedTag = (tag) => {
  if (!currentSessionTags.value.includes(tag)) {
    currentSessionTags.value.push(tag)
    chatStore.addSessionTag(managingSessionId.value, tag)
    ElMessage.success(`标签 "${tag}" 已添加`)
  }
}

const removeTag = (tag) => {
  const index = currentSessionTags.value.indexOf(tag)
  if (index !== -1) {
    currentSessionTags.value.splice(index, 1)
    chatStore.removeSessionTag(managingSessionId.value, tag)
    ElMessage.success(`标签 "${tag}" 已移除`)
  }
}

// 工具函数
const formatTime = (timestamp) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now - time
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}


// 初始化
const initialize = () => {
  applyFilters()
}

// 监听会话变化
watch(() => chatStore.sessionHistory, () => {
  applyFilters()
}, { deep: true })

// 组件挂载时初始化
initialize()
</script>

<style scoped>
.chat-history {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
  border-radius: 0;
  overflow: hidden;
}

.history-header-card {
  margin: 10px 12px 8px 12px;
  border-radius: 12px;
  background: var(--ops-surface);
  border: 1px solid var(--ops-border);
  border-top: 3px solid var(--ops-accent);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
  position: sticky;
  top: 0;
  z-index: 2;
}

.history-header-card:hover {
  box-shadow: none;
  border-color: var(--ops-accent-border);
}

.history-header-card {
  padding: 12px 12px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 650;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.search-section-card {
  margin: 0 12px 10px 12px;
  border-radius: 12px;
  background: transparent;
  border: none;
  box-shadow: none;
  position: sticky;
  top: 54px;
  z-index: 2;
}

.search-section-card {
  padding: 0;
}

.search-section {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.search-input :deep(.el-input__inner) {
  border-radius: 10px;
  border: 1px solid var(--ops-border);
  background: var(--ops-surface-raised);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.search-input :deep(.el-input__inner):focus {
  border-color: var(--ops-accent-border);
  box-shadow: 0 0 0 3px var(--ops-accent-soft);
}

.filter-badge {
  margin-left: 4px;
}

.filters-panel {
  padding: 16px;
  border-bottom: 1px solid var(--ops-border);
  background-color: var(--ops-surface);
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.filter-row label {
  width: 80px;
  font-size: 14px;
  color: var(--text-secondary);
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px 12px;
}

.session-card {
  margin-bottom: 8px;
  border-radius: 12px;
  background: var(--ops-surface);
  border: 1px solid var(--ops-border);
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, background-color 0.15s ease;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  position: relative;
}

/* 为不同位置的卡片添加不同颜色的边框 */
.session-card:nth-child(6n+1) {
  border-left: 3px solid var(--primary-color);
}

.session-card:nth-child(6n+2) {
  border-left: 3px solid var(--purple-color);
}

.session-card:nth-child(6n+3) {
  border-left: 3px solid var(--teal-color);
}

.session-card:nth-child(6n+4) {
  border-left: 3px solid var(--orange-color);
}

.session-card:nth-child(6n+5) {
  border-left: 3px solid var(--pink-color);
}

.session-card:nth-child(6n+6) {
  border-left: 3px solid var(--cyan-color);
}

.session-card:hover {
  border-color: var(--ops-accent-border);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10);
  transform: translateX(2px);
}

.session-card-active {
  background: var(--ops-surface-selected);
  border-color: var(--ops-accent-border);
  border-left-width: 4px !important;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10);
}

.session-card-active .session-title,
.session-card-active .last-activity {
  color: var(--ops-text) !important;
}

.session-card-active .item-icon {
  color: var(--ops-accent) !important;
}

.session-card {
  padding: 12px 12px;
}

.session-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.session-title-container {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.item-icon {
  font-size: 18px;
  color: #667eea;
  margin-top: 2px;
  flex-shrink: 0;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  cursor: text;
  word-break: break-word;
}

.title-edit {
  margin-bottom: 4px;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
}

.meta-tag {
  font-size: 11px;
}

.last-activity {
  color: var(--text-secondary);
  font-size: 11px;
}

.session-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.session-tags {
  margin: 8px 0 4px 0;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.session-tag {
  font-size: 11px;
}


.empty-state {
  padding: 40px 20px;
  text-align: center;
}

/* 标签管理对话框 */
.tag-management {
  padding: 16px 0;
}

.tag-management h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.tags-container {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.tag-item {
  margin-bottom: 4px;
}

.suggested-tag {
  cursor: pointer;
  margin-bottom: 4px;
}

.suggested-tag:hover {
  opacity: 0.8;
}

.add-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-section {
    flex-direction: column;
  }

  .filter-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .filter-row label {
    width: auto;
  }

  .session-main {
    flex-direction: column;
    gap: 8px;
  }

  .session-meta {
    flex-direction: column;
    gap: 4px;
  }
}

/* Chat cockpit compact sidebar */
.chat-history {
  color: var(--ops-text);
}

.history-header-card {
  margin: 10px 12px 8px !important;
  padding: 12px !important;
  border: 1px solid var(--ops-border) !important;
  border-radius: 8px !important;
  background: var(--ops-surface) !important;
  box-shadow: none !important;
}

.history-header-card:hover {
  border-color: var(--ops-accent-border) !important;
  box-shadow: none !important;
}

.header-content {
  align-items: stretch !important;
  flex-direction: column !important;
  gap: 10px !important;
}

.header-title {
  justify-content: space-between;
  gap: 8px !important;
  min-width: 0;
}

.header-title h3 {
  min-width: max-content;
  color: var(--ops-text) !important;
  font-size: 14px !important;
  letter-spacing: 0 !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  word-break: keep-all !important;
}

.header-title :deep(.el-tag) {
  flex: 0 0 auto;
  border-color: var(--ops-accent-border) !important;
  background: var(--ops-accent-soft) !important;
  color: var(--ops-accent-strong) !important;
}

.header-actions {
  justify-content: flex-end;
  gap: 8px !important;
}

.header-actions :deep(.el-button) {
  border-color: var(--ops-border) !important;
  background: var(--ops-surface-raised) !important;
  color: var(--ops-text-soft) !important;
}

.header-actions :deep(.el-button--primary) {
  border-color: var(--ops-accent-border) !important;
  background: var(--ops-accent-soft) !important;
  color: var(--ops-accent-strong) !important;
}

.search-section-card {
  margin: 0 12px 10px !important;
}

.search-section {
  align-items: center;
}

.search-input :deep(.el-input__wrapper) {
  border: 1px solid var(--ops-border) !important;
  border-radius: 8px !important;
  background: var(--ops-bg-elevated) !important;
  box-shadow: none !important;
}

.search-input :deep(.el-input__inner) {
  color: var(--ops-text) !important;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: var(--ops-muted-2) !important;
}

.search-section :deep(.el-button) {
  border-color: var(--ops-border) !important;
  border-radius: 8px !important;
  background: var(--ops-bg-elevated) !important;
  color: var(--ops-muted) !important;
}

.sessions-list {
  padding: 0 12px 12px !important;
}

.session-card {
  padding: 12px !important;
  border: 1px solid var(--ops-border) !important;
  border-left: 1px solid var(--ops-border) !important;
  border-radius: 8px !important;
  background: var(--ops-surface) !important;
  box-shadow: none !important;
}

.session-card:hover {
  border-color: var(--ops-accent-border) !important;
  box-shadow: none !important;
  transform: none !important;
}

.session-card-active {
  border-color: var(--ops-accent-border) !important;
  background: var(--ops-surface-selected) !important;
}

.session-title {
  color: var(--ops-text) !important;
  font-size: 14px !important;
  line-height: 1.35 !important;
}

.session-preview {
  display: -webkit-box;
  margin-top: 4px;
  overflow: hidden;
  color: var(--ops-muted);
  font-size: 12px;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.session-card-active .session-title,
.session-card-active .last-activity {
  color: var(--ops-text) !important;
}

.session-meta {
  gap: 8px !important;
  margin-top: 8px !important;
  color: var(--ops-muted-2) !important;
  font-size: 11px !important;
}

.session-meta :deep(.el-tag) {
  border-color: var(--ops-accent-border) !important;
  background: var(--ops-accent-soft) !important;
  color: var(--ops-accent-strong) !important;
}

.last-activity {
  color: var(--ops-muted-2) !important;
}

.item-icon,
.session-card-active .item-icon {
  color: var(--ops-accent) !important;
}

.session-actions :deep(.el-button) {
  border-radius: 6px !important;
  background: var(--ops-surface-raised) !important;
  color: var(--ops-text-soft) !important;
}
</style>
