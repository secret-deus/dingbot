<template>
  <div class="mcp-config-page mcp-cockpit">
    <section class="mcp-command-strip">
      <div class="command-copy">
        <p class="eyebrow">LOCAL TOOL FABRIC</p>
        <h1>MCP 配置管理</h1>
        <span>统一管理本地工具服务器、工具开关和配置校验，让智能对话使用同一套受控工具总线。</span>
      </div>
      <div class="command-actions">
        <el-button type="primary" :loading="loadingServers || loadingTools" @click="refreshAll">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
        <el-button :loading="validating" @click="validateConfig">
          <el-icon><Check /></el-icon>
          验证配置
        </el-button>
      </div>
    </section>

    <section class="metric-strip">
      <div class="metric-tile accent">
        <span>Servers</span>
        <strong>{{ servers.length }}</strong>
        <em>{{ enabledServers }} enabled</em>
      </div>
      <div class="metric-tile">
        <span>Tools</span>
        <strong>{{ tools.length }}</strong>
        <em>{{ enabledTools }} enabled</em>
      </div>
      <div class="metric-tile warning">
        <span>Warnings</span>
        <strong>{{ validationResult?.warnings?.length || 0 }}</strong>
        <em>last validation</em>
      </div>
      <div class="metric-tile success">
        <span>Config</span>
        <strong>{{ validationStateText }}</strong>
        <em>runtime health</em>
      </div>
    </section>

    <section class="mcp-shell">
      <aside class="mcp-rail">
        <div class="rail-card">
          <p class="eyebrow">WORKSPACE</p>
          <div class="segmented-nav">
            <button :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">运行概览</button>
            <button :class="{ active: activeTab === 'llm' }" @click="activeTab = 'llm'">LLM 设置</button>
            <button :class="{ active: activeTab === 'editor' }" @click="activeTab = 'editor'">配置编辑</button>
            <button :class="{ active: activeTab === 'servers' }" @click="activeTab = 'servers'">服务器</button>
            <button :class="{ active: activeTab === 'tools' }" @click="activeTab = 'tools'">工具目录</button>
            <button :class="{ active: activeTab === 'validation' }" @click="activeTab = 'validation'">配置验证</button>
          </div>
        </div>

        <div class="rail-card">
          <p class="eyebrow">CONTROL</p>
          <div class="control-stack">
            <button @click="loadServers">刷新服务器</button>
            <button @click="loadTools">刷新工具</button>
            <button @click="refreshTools">重新加载工具</button>
          </div>
        </div>
      </aside>

      <main class="mcp-stage">
        <section v-if="activeTab === 'overview'" class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">RUNTIME OVERVIEW</p>
              <h2>运行概览</h2>
              <span>快速查看服务器启用状态、工具数量和最近一次配置校验结果。</span>
            </div>
          </div>

          <div class="overview-grid">
            <article v-for="server in servers" :key="server.name" class="server-card">
              <div class="server-head">
                <div>
                  <h3>{{ server.name }}</h3>
                  <span>{{ server.type || 'mcp-server' }}</span>
                </div>
                <span class="state-pill" :class="{ on: server.enabled }">
                  {{ server.enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
              <div class="server-meta">
                <div>
                  <span>Tools</span>
                  <strong>{{ server.tools_count || 0 }}</strong>
                </div>
                <div>
                  <span>Runtime</span>
                  <strong>{{ server.enabled ? 'Ready' : 'Paused' }}</strong>
                </div>
              </div>
              <div class="server-actions">
                <el-button size="small" :type="server.enabled ? 'warning' : 'success'" plain @click="toggleServer(server.name)">
                  {{ server.enabled ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="primary" plain @click="testConnection(server.name)">测试连接</el-button>
              </div>
            </article>

            <div v-if="servers.length === 0 && !loadingServers" class="empty-cockpit">
              <strong>暂无 MCP 服务器</strong>
              <span>可以在配置编辑中添加本地或远程 MCP 服务。</span>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'llm'" class="stage-panel config-embed-panel">
          <LLMConfig />
        </section>

        <section v-else-if="activeTab === 'editor'" class="stage-panel editor-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">CONFIG EDITOR</p>
              <h2>配置编辑</h2>
              <span>编辑服务器、工具暴露范围和运行参数。</span>
            </div>
          </div>
          <MCPConfigEditor />
        </section>

        <section v-else-if="activeTab === 'servers'" class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">SERVER CONTROL</p>
              <h2>服务器</h2>
              <span>启用、禁用或测试单个 MCP 服务器。</span>
            </div>
            <el-button :loading="loadingServers" @click="loadServers">刷新服务器</el-button>
          </div>

          <div v-if="serverError" class="error-banner">{{ serverError }}</div>
          <div v-loading="loadingServers" class="server-list">
            <article v-for="server in servers" :key="server.name" class="server-row">
              <div>
                <h3>{{ server.name }}</h3>
                <span>{{ server.type || 'mcp-server' }} · {{ server.tools_count || 0 }} tools</span>
              </div>
              <span class="state-pill" :class="{ on: server.enabled }">
                {{ server.enabled ? '启用' : '禁用' }}
              </span>
              <div class="row-actions">
                <el-button size="small" :type="server.enabled ? 'warning' : 'success'" plain @click="toggleServer(server.name)">
                  {{ server.enabled ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="primary" plain @click="testConnection(server.name)">测试</el-button>
              </div>
            </article>
            <div v-if="servers.length === 0 && !loadingServers" class="empty-cockpit">暂无服务器配置</div>
          </div>
        </section>

        <section v-else-if="activeTab === 'tools'" class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">TOOL DIRECTORY</p>
              <h2>工具目录</h2>
              <span>管理工具暴露状态，避免智能对话调用不需要的能力。</span>
            </div>
            <div class="command-actions">
              <el-button :loading="loadingTools" @click="loadTools">刷新工具</el-button>
              <el-button type="primary" :loading="refreshingTools" @click="refreshTools">
                <el-icon><RefreshRight /></el-icon>
                重新加载
              </el-button>
            </div>
          </div>

          <div v-if="toolsError" class="error-banner">{{ toolsError }}</div>
          <div v-loading="loadingTools" class="tool-grid">
            <article v-for="tool in tools" :key="tool.name" class="tool-card">
              <div class="tool-head">
                <h3>{{ tool.name }}</h3>
                <span class="state-pill" :class="{ on: tool.enabled }">
                  {{ tool.enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
              <p>{{ tool.description || '暂无描述' }}</p>
              <div class="tool-meta">
                <span>{{ tool.category || 'general' }}</span>
                <span>{{ tool.server || 'local' }}</span>
              </div>
              <el-button size="small" :type="tool.enabled ? 'warning' : 'success'" plain @click="toggleTool(tool.name)">
                {{ tool.enabled ? '禁用工具' : '启用工具' }}
              </el-button>
            </article>
            <div v-if="tools.length === 0 && !loadingTools" class="empty-cockpit">暂无工具配置</div>
          </div>
        </section>

        <section v-else class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">VALIDATION</p>
              <h2>配置验证</h2>
              <span>检查配置结构、服务器连通性和工具注册状态。</span>
            </div>
            <el-button type="primary" :loading="validating" @click="validateConfig">
              <el-icon><Check /></el-icon>
              验证配置
            </el-button>
          </div>

          <div v-loading="validating" class="validation-board">
            <div v-if="validationError" class="error-banner">{{ validationError }}</div>
            <template v-else-if="validationResult">
              <div class="validation-hero" :class="{ ok: validationResult.valid }">
                <strong>{{ validationResult.valid ? '配置验证通过' : '配置存在问题' }}</strong>
                <span>{{ validationResult.valid ? '所有配置项验证通过' : '请根据错误和警告调整配置' }}</span>
              </div>

              <div class="validation-grid">
                <div class="validation-section">
                  <h3>错误 {{ validationResult.errors?.length || 0 }}</h3>
                  <div v-if="!validationResult.errors?.length" class="empty-inline">无错误</div>
                  <div v-for="(error, index) in validationResult.errors" :key="'error-' + index" class="issue error">
                    {{ error }}
                  </div>
                </div>
                <div class="validation-section">
                  <h3>警告 {{ validationResult.warnings?.length || 0 }}</h3>
                  <div v-if="!validationResult.warnings?.length" class="empty-inline">无警告</div>
                  <div v-for="(warning, index) in validationResult.warnings" :key="'warning-' + index" class="issue warning">
                    {{ warning }}
                  </div>
                </div>
              </div>

              <div class="server-status-grid">
                <article v-for="(status, server) in validationResult.server_status" :key="server" class="server-status-card">
                  <span>{{ server }}</span>
                  <strong :class="status === 'connected' ? 'ok' : 'bad'">
                    {{ status === 'connected' ? '已连接' : '连接失败' }}
                  </strong>
                </article>
              </div>
            </template>

            <div v-else class="empty-cockpit">
              <strong>等待配置验证</strong>
              <span>点击验证配置，查看服务器和工具状态。</span>
            </div>
          </div>
        </section>
      </main>
    </section>

    <!-- 连接测试结果对话框 -->
    <el-dialog
      v-model="connectionTestVisible"
      :title="connectionTestResult ? '连接测试结果' : '测试中...'"
      width="400px"
    >
      <div v-if="connectionTestResult" class="connection-test-result">
        <el-result
          :icon="connectionTestResult.connected ? 'success' : 'error'"
          :title="connectionTestResult.connected ? '连接成功' : '连接失败'"
          :sub-title="connectionTestResult.message"
        >
          <template #extra>
            <div class="connection-details">
              <p><strong>服务器:</strong> {{ connectionTestResult.server_name }}</p>
              <p><strong>状态:</strong> {{ connectionTestResult.status }}</p>
            </div>
          </template>
        </el-result>
      </div>

      <div v-else class="connection-test-loading">
        <el-skeleton :rows="3" animated />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, RefreshRight, Check } from '@element-plus/icons-vue'
import apiClient from '@/api/client'
import MCPConfigEditor from '@/components/MCPConfigEditor.vue'
import LLMConfig from '@/views/LLMConfig.vue'

// 响应式状态
const route = useRoute()
const initialTab = ['overview', 'llm', 'editor', 'servers', 'tools', 'validation'].includes(route.query.tab)
  ? route.query.tab
  : 'overview'
const activeTab = ref(initialTab)

// 服务器管理
const servers = ref([])
const loadingServers = ref(false)
const serverError = ref(null)

// 工具管理
const tools = ref([])
const loadingTools = ref(false)
const refreshingTools = ref(false)
const toolsError = ref(null)

// 配置验证
const validationResult = ref(null)
const validating = ref(false)
const validationError = ref(null)

// 连接测试
const connectionTestVisible = ref(false)
const connectionTestResult = ref(null)
const testingConnection = ref(false)

// 方法
const refreshPage = () => {
  window.location.reload()
}

const enabledServers = computed(() => servers.value.filter((server) => server.enabled).length)
const enabledTools = computed(() => tools.value.filter((tool) => tool.enabled).length)
const validationStateText = computed(() => {
  if (!validationResult.value) return 'READY'
  return validationResult.value.valid ? 'PASS' : 'WARN'
})

const refreshAll = async () => {
  await Promise.all([loadServers(), loadTools()])
}

const loadServers = async () => {
  loadingServers.value = true
  serverError.value = null

  try {
    const response = await apiClient.get('/v2/mcp/config/servers')
    servers.value = response.data
  } catch (e) {
    console.error('加载服务器失败:', e)
    serverError.value = e.response?.data?.error?.message || e.response?.data?.detail || e.message || '未知错误'
  } finally {
    loadingServers.value = false
  }
}

const loadTools = async () => {
  loadingTools.value = true
  toolsError.value = null

  try {
    const response = await apiClient.get('/v2/mcp/config/tools')
    tools.value = response.data
  } catch (e) {
    console.error('加载工具失败:', e)
    toolsError.value = e.response?.data?.error?.message || e.response?.data?.detail || e.message || '未知错误'
  } finally {
    loadingTools.value = false
  }
}

const refreshTools = async () => {
  refreshingTools.value = true
  toolsError.value = null

  try {
    const response = await apiClient.post('/v2/tools/refresh')
    if (response.data.success) {
      ElMessage.success(response.data.message)
      // 重新加载工具列表
      await loadTools()
    } else {
      ElMessage.error(response.data.error || '刷新工具列表失败')
    }
  } catch (e) {
    console.error('刷新工具失败:', e)
    toolsError.value = e.response?.data?.error?.message || e.response?.data?.detail || e.message || '刷新失败'
    ElMessage.error('刷新工具列表失败')
  } finally {
    refreshingTools.value = false
  }
}

const toggleServer = async (serverName) => {
  try {
    const response = await apiClient.post(`/v2/mcp/config/servers/${serverName}/toggle`)
    ElMessage.success(response.data.message)
    await loadServers()
  } catch (e) {
    console.error('切换服务器状态失败:', e)
    ElMessage.error(e.response?.data?.error?.message || e.response?.data?.detail || e.message || '操作失败')
  }
}

const toggleTool = async (toolName) => {
  try {
    const response = await apiClient.post(`/v2/mcp/config/tools/${toolName}/toggle`)
    ElMessage.success(response.data.message)
    await loadTools()
  } catch (e) {
    console.error('切换工具状态失败:', e)
    ElMessage.error(e.response?.data?.error?.message || e.response?.data?.detail || e.message || '操作失败')
  }
}

const validateConfig = async () => {
  validating.value = true
  validationError.value = null
  validationResult.value = null

  try {
    const response = await apiClient.post('/v2/mcp/config/validate')
    validationResult.value = response.data
  } catch (e) {
    console.error('配置验证失败:', e)
    validationError.value = e.response?.data?.error?.message || e.response?.data?.detail || e.message || '未知错误'
  } finally {
    validating.value = false
  }
}

const testConnection = async (serverName) => {
  connectionTestVisible.value = true
  connectionTestResult.value = null
  testingConnection.value = true

  try {
    const response = await apiClient.post(`/v2/mcp/config/test/${serverName}`)
    connectionTestResult.value = response.data
  } catch (e) {
    console.error('连接测试失败:', e)
    connectionTestResult.value = {
      server_name: serverName,
      status: 'error',
      connected: false,
      message: e.response?.data?.error?.message || e.response?.data?.detail || e.message || '测试失败'
    }
  } finally {
    testingConnection.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.mcp-config-page {
  min-height: 100%;
  padding: 24px;
  color: #f1efe7;
  background: #090a08;
}

.mcp-command-strip {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 22px 24px;
  border: 1px solid rgba(214, 168, 79, 0.2);
  background: #12140f;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.28);
  border-radius: 10px;
  margin-bottom: 18px;
}

.command-copy h1,
.stage-head h2 {
  margin: 0;
  color: #f8fbff;
  letter-spacing: 0;
}

.command-copy h1 {
  font-size: 30px;
  line-height: 1.15;
}

.command-copy span,
.stage-head span,
.metric-tile em,
.server-head span,
.server-row span,
.tool-card p,
.tool-meta,
.empty-cockpit span {
  color: #8ea5b8;
  font-style: normal;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #d6a84f;
}

.command-actions,
.server-actions,
.row-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.metric-tile,
.rail-card,
.stage-panel,
.server-card,
.tool-card,
.runtime-card,
.server-status-card {
  border: 1px solid rgba(148, 148, 132, 0.16);
  background: #12140f;
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
}

.metric-tile {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.metric-tile span,
.server-meta span,
.server-status-card span {
  color: #8aa0b2;
  font-size: 12px;
}

.metric-tile strong {
  color: #d6a84f;
  font-size: 30px;
  line-height: 1;
}

.metric-tile.warning strong {
  color: #fbbf24;
}

.metric-tile.success strong {
  color: #8bff9b;
}

.mcp-shell {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.mcp-rail {
  display: grid;
  gap: 12px;
  position: sticky;
  top: 16px;
}

.rail-card {
  padding: 16px;
}

.segmented-nav,
.control-stack {
  display: grid;
  gap: 8px;
}

.segmented-nav button,
.control-stack button {
  width: 100%;
  border: 1px solid rgba(214, 168, 79, 0.18);
  background: #151712;
  color: #b9c8d8;
  border-radius: 8px;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
}

.segmented-nav button.active {
  color: #031016;
  background: #d6a84f;
  border-color: transparent;
  font-weight: 700;
}

.stage-panel {
  padding: 18px;
  min-height: 560px;
}

.stage-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(148, 148, 132, 0.14);
  margin-bottom: 16px;
}

.stage-head h2 {
  font-size: 22px;
}

.overview-grid,
.tool-grid,
.validation-grid,
.server-status-grid {
  display: grid;
  gap: 12px;
}

.overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.tool-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.validation-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.server-status-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 12px;
}

.server-card,
.tool-card,
.server-status-card {
  padding: 14px;
}

.server-head,
.tool-head,
.server-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.server-head h3,
.server-row h3,
.tool-head h3,
.validation-section h3 {
  margin: 0 0 4px;
  color: #eef7ff;
  font-size: 15px;
}

.server-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
}

.server-meta > div {
  display: grid;
  gap: 4px;
  padding: 10px;
  background: #151712;
  border-radius: 8px;
}

.server-meta strong,
.server-status-card strong {
  color: #d9edf7;
}

.state-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  color: #9fb2c5;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.18);
  font-size: 12px;
  font-weight: 700;
}

.state-pill.on {
  color: #052414;
  background: #8bff9b;
  border-color: transparent;
}

.server-list {
  display: grid;
  gap: 10px;
}

.server-row {
  align-items: center;
  padding: 14px;
  border: 1px solid rgba(148, 148, 132, 0.14);
  background: #151712;
  border-radius: 9px;
}

.tool-card {
  display: grid;
  gap: 12px;
  align-content: start;
}

.tool-card p {
  margin: 0;
  min-height: 42px;
  font-size: 13px;
  line-height: 1.55;
}

.tool-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
}

.validation-hero {
  display: grid;
  gap: 6px;
  padding: 18px;
  margin-bottom: 12px;
  border-radius: 10px;
  border: 1px solid rgba(251, 191, 36, 0.24);
  background: rgba(120, 53, 15, 0.18);
}

.validation-hero.ok {
  border-color: rgba(139, 255, 155, 0.28);
  background: rgba(20, 83, 45, 0.18);
}

.validation-hero strong {
  color: #f8fbff;
  font-size: 18px;
}

.validation-section {
  padding: 14px;
  border: 1px solid rgba(148, 148, 132, 0.16);
  background: #151712;
  border-radius: 9px;
}

.issue {
  padding: 10px;
  border-radius: 8px;
  margin-top: 8px;
  color: #d9edf7;
  font-size: 13px;
}

.issue.error {
  background: rgba(244, 63, 94, 0.14);
  color: #fecdd3;
}

.issue.warning {
  background: rgba(251, 191, 36, 0.14);
  color: #fde68a;
}

.server-status-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.ok {
  color: #8bff9b;
}

.bad {
  color: #fb7185;
}

.error-banner {
  padding: 12px;
  margin-bottom: 12px;
  color: #fecdd3;
  background: rgba(244, 63, 94, 0.14);
  border: 1px solid rgba(244, 63, 94, 0.24);
  border-radius: 8px;
}

.empty-cockpit,
.empty-inline {
  min-height: 180px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  text-align: center;
  color: #c7d8e6;
}

.empty-inline {
  min-height: 64px;
  color: #8aa0b2;
}

.editor-panel :deep(.mcp-config-editor),
.editor-panel :deep(.el-card) {
  background: #151712;
  border-color: rgba(148, 148, 132, 0.16);
  color: #d9edf7;
}

.mcp-cockpit :deep(.el-button) {
  border-radius: 8px;
  border-color: #3a3d30 !important;
  background: #151712 !important;
  color: #e6e2d8 !important;
  font-weight: 800;
  box-shadow: none !important;
}

.mcp-cockpit :deep(.el-button:hover) {
  border-color: rgba(214, 168, 79, 0.42) !important;
  background: rgba(214, 168, 79, 0.1) !important;
  color: #e4bd68 !important;
}

.mcp-cockpit :deep(.el-button--primary),
.mcp-cockpit :deep(.el-button--warning),
.mcp-cockpit :deep(.el-button--success) {
  border-color: rgba(214, 168, 79, 0.34) !important;
  background: rgba(214, 168, 79, 0.1) !important;
  color: #e4bd68 !important;
}

.mcp-cockpit :deep(.el-input__wrapper),
.mcp-cockpit :deep(.el-select__wrapper) {
  background: #10120e;
  border-color: rgba(148, 148, 132, 0.18);
  box-shadow: 0 0 0 1px rgba(148, 148, 132, 0.16) inset;
}

.mcp-cockpit :deep(.el-input__inner),
.mcp-cockpit :deep(.el-select__placeholder) {
  color: #b9c8d8;
}

.connection-details {
  text-align: left;
  margin-top: 20px;
}

.connection-test-loading {
  padding: 20px;
}

@media (max-width: 1180px) {
  .metric-strip,
  .overview-grid,
  .tool-grid,
  .validation-grid,
  .server-status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mcp-shell {
    grid-template-columns: 1fr;
  }

  .mcp-rail {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .mcp-config-page {
    padding: 14px;
  }

  .mcp-command-strip,
  .stage-head,
  .server-row {
    flex-direction: column;
    align-items: stretch;
  }

  .metric-strip,
  .overview-grid,
  .tool-grid,
  .validation-grid,
  .server-status-grid,
  .mcp-rail {
    grid-template-columns: 1fr;
  }
}
</style>
