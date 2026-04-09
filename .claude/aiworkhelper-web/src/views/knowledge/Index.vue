<template>
  <div class="knowledge-page">
    <el-card class="knowledge-container">
      <template #header>
        <div class="knowledge-header">
          <span>知识库</span>
          <el-tag type="info" size="small">AI智能问答</el-tag>
        </div>
      </template>

      <div class="knowledge-content">
        <!-- 左侧：文件管理区域 -->
        <div class="upload-section">
          <el-card shadow="hover">
            <template #header>
              <div class="section-title">
                <el-icon><Upload /></el-icon>
                <span>上传文档</span>
              </div>
            </template>

            <el-upload
              class="upload-dragger"
              drag
              :before-upload="handleUploadFile"
              :show-file-list="false"
              accept=".pdf,.docx,.txt,.md"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                拖拽文件到此处或
                <em>点击上传</em>
              </div>
              <div class="upload-tip">
                支持 PDF、Word、TXT、Markdown 格式文件
              </div>
            </el-upload>

            <div v-if="uploadedFiles.length > 0" class="file-list">
              <div class="file-list-header">
                <span>已上传文件</span>
                <el-tag size="small">{{ uploadedFiles.length }}</el-tag>
              </div>
              <div
                v-for="file in uploadedFiles"
                :key="file.id"
                class="file-item"
              >
                <el-icon><Document /></el-icon>
                <div class="file-info">
                  <div class="file-name">{{ file.filename }}</div>
                  <div class="file-time">{{ formatTime(file.uploadTime) }}</div>
                </div>
                <el-tag
                  v-if="file.status === 0"
                  type="warning"
                  size="small"
                >
                  待处理
                </el-tag>
                <el-tag
                  v-else-if="file.status === 1"
                  type="success"
                  size="small"
                >
                  已入库
                </el-tag>
                <el-tag
                  v-else-if="file.status === 2"
                  type="danger"
                  size="small"
                >
                  处理失败
                </el-tag>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleDeleteFile(file.id)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card shadow="hover" class="tips-card">
            <template #header>
              <div class="section-title">
                <el-icon><InfoFilled /></el-icon>
                <span>使用说明</span>
              </div>
            </template>
            <div class="tips-content">
              <p>1. 上传文档后，在右侧发送"更新知识库"</p>
              <p>2. 更新成功后，可直接提问文档内容</p>
              <p>3. AI 基于文档内容进行智能回答</p>
              <p>4. 支持员工手册、规章制度等文档</p>
            </div>
          </el-card>
        </div>

        <!-- 右侧：AI 对话区域（SSE 流式） -->
        <div class="chat-section">
          <el-card class="chat-card" body-style="padding: 0; height: 100%;">
            <template #header>
              <div class="chat-header">
                <span>AI 知识库助手</span>
                <el-tag type="success" size="small">在线</el-tag>
              </div>
            </template>

            <div class="chat-container">
              <!-- 消息列表 -->
              <div ref="messageListRef" class="message-list" @click="handleMessageClick">
                <div
                  v-for="(msg, index) in messages"
                  :key="index"
                  :class="['message-item', msg.isSelf ? 'self' : 'other']"
                >
                  <el-avatar :size="36">
                    {{ msg.isSelf ? userStore.userInfo?.name?.[0] : 'AI' }}
                  </el-avatar>
                  <div class="message-content">
                    <div class="message-meta">
                      <span class="sender-name">{{ msg.isSelf ? '我' : 'AI助手' }}</span>
                      <span class="message-time">{{ formatMessageTime(msg.time) }}</span>
                    </div>
                    <div class="message-bubble">
                      <div class="text-message" v-html="renderMessage(msg.content)"></div>
                    </div>
                  </div>
                </div>

                <div v-if="aiLoading" class="message-item other">
                  <el-avatar :size="36">AI</el-avatar>
                  <div class="message-content">
                    <div class="message-bubble">
                      <el-icon class="is-loading"><Loading /></el-icon>
                      AI正在思考中...
                    </div>
                  </div>
                </div>
              </div>

              <!-- 工具调用状态 -->
              <div v-if="toolCalls.length > 0" class="tool-call-bar">
                <div v-for="(tc, i) in toolCalls" :key="i" class="tool-call-item">
                  <el-icon class="is-loading" v-if="tc.status === 'running'"><Loading /></el-icon>
                  <el-icon v-else><CircleCheck /></el-icon>
                  <span>{{ tc.tool }} - {{ tc.status }}</span>
                </div>
              </div>

              <!-- 输入区域 -->
              <div class="message-input-area">
                <div class="input-box">
                  <el-input
                    ref="inputRef"
                    v-model="inputMessage"
                    type="textarea"
                    :rows="3"
                    placeholder="例如: 更新知识库 / 请假流程是什么？"
                    @keydown.enter.ctrl="handleSend"
                    :disabled="aiLoading"
                  />
                  <el-button
                    type="primary"
                    :loading="aiLoading"
                    @click="handleSend"
                  >
                    发送 (Ctrl+Enter)
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>

    <!-- 文档预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="70%"
      top="5vh"
      destroy-on-close
    >
      <div v-if="previewLoading" class="preview-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <pre v-else class="preview-content">{{ previewContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Document,
  InfoFilled,
  Loading,
  CircleCheck
} from '@element-plus/icons-vue'
import {
  uploadKnowledgeFile,
  getKnowledgeList,
  deleteKnowledge,
  getKnowledgeFileContent,
  type KnowledgeDocument
} from '@/api/knowledge'
import { chatStream, createAIConversation, type SSECallbacks } from '@/api/chat'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

const userStore = useUserStore()

// ========== 对话状态 ==========
interface Message {
  content: string
  time: number
  isSelf: boolean
}

const messageListRef = ref<HTMLElement>()
const inputRef = ref()
const messages = ref<Message[]>([
  {
    content: '你好！我是知识库AI助手。你可以上传文档后让我更新知识库，或者直接向我提问已有知识库中的内容。',
    time: Date.now() / 1000,
    isSelf: false
  }
])
const inputMessage = ref('')
const aiLoading = ref(false)
const conversationId = ref('')
const toolCalls = ref<Array<{ tool: string; status: string }>>([])

// ========== 文件状态 ==========
const uploadedFiles = ref<KnowledgeDocument[]>([])

// ========== 生命周期 ==========
onMounted(async () => {
  // 创建专用 AI 会话
  try {
    const res = await createAIConversation('知识库对话')
    if (res.code === 200 && res.data?.data) {
      conversationId.value = res.data.data.id
    }
  } catch (e) {
    console.error('创建知识库会话失败:', e)
  }
  // 加载已有文档列表
  await loadFileList()
})

// ========== 文件操作 ==========
const loadFileList = async () => {
  try {
    const res = await getKnowledgeList(1, 50)
    if (res.code === 200 && res.data) {
      uploadedFiles.value = res.data.list || []
    }
  } catch {
    // 静默失败
  }
}

const handleUploadFile = async (file: File) => {
  try {
    ElMessage.info('正在上传文件...')
    const res = await uploadKnowledgeFile(file)
    if (res.code === 200 && res.data) {
      uploadedFiles.value.unshift(res.data)
      ElMessage.success('文件上传成功！')
      // 添加提示消息
      messages.value.push({
        content: `文件 "${file.name}" 已上传成功。请发送"更新知识库"让我处理文档内容。`,
        time: Date.now() / 1000,
        isSelf: false
      })
      // 自动填充指令
      inputMessage.value = '根据我上传的文件更新知识库'
      scrollToBottom()
    }
  } catch {
    ElMessage.error('文件上传失败')
  }
  return false
}

const handleDeleteFile = async (docId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？关联的知识数据也会被清除。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await deleteKnowledge(docId)
    if (res.code === 200) {
      uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== docId)
      ElMessage.success('文档已删除')
    }
  } catch {
    // 用户取消
  }
}

// ========== 对话操作 ==========
const handleSend = async () => {
  if (!inputMessage.value.trim() || aiLoading.value) return
  if (!conversationId.value) {
    ElMessage.error('会话未就绪，请刷新页面重试')
    return
  }

  const content = inputMessage.value.trim()
  messages.value.push({ content, time: Date.now() / 1000, isSelf: true })
  inputMessage.value = ''
  scrollToBottom()

  aiLoading.value = true
  toolCalls.value = []
  let aiContent = ''

  const callbacks: SSECallbacks = {
    onChunk: (chunk) => {
      aiContent += chunk
      // 更新最后一条 AI 消息内容
      updateOrCreateAiMessage(aiContent)
    },
    onToolCall: (tool, _args, status) => {
      toolCalls.value.push({ tool, status })
      // 文件状态刷新（updateKnowledge 完成后）
      if (tool === 'updateKnowledge' && status === 'running') {
        loadFileList()
      }
    },
    onToolResult: (tool, _result, status) => {
      const tc = toolCalls.value.find(t => t.tool === tool && t.status === 'running')
      if (tc) tc.status = status
      // 更新完成后刷新文件列表
      if (tool === 'updateKnowledge') {
        setTimeout(loadFileList, 1000)
      }
    },
    onComplete: (fullContent) => {
      aiLoading.value = false
      toolCalls.value = []
      // 确保最终内容完整
      updateOrCreateAiMessage(fullContent || aiContent, true)
      // 刷新文件列表状态
      loadFileList()
    },
    onError: (errorCode, message) => {
      aiLoading.value = false
      toolCalls.value = []
      if (errorCode === 'UNAUTHORIZED') {
        ElMessage.error('登录已过期，请重新登录')
      } else {
        updateOrCreateAiMessage(`抱歉，处理出现了问题: ${message}`)
      }
    }
  }

  try {
    await chatStream(conversationId.value, content, callbacks)
  } catch (e: any) {
    aiLoading.value = false
    updateOrCreateAiMessage('抱歉，请求失败了。请稍后重试。')
  }
}

/**
 * 更新或创建 AI 回复消息（支持流式追加）
 */
const updateOrCreateAiMessage = (content: string, isFinal = false) => {
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && !lastMsg.isSelf && !isFinal) {
    // 更新已有的 AI 消息（流式追加）
    lastMsg.content = content
  } else if (isFinal) {
    // 最终内容：更新最后一条 AI 消息
    if (lastMsg && !lastMsg.isSelf) {
      lastMsg.content = content
    } else {
      messages.value.push({
        content,
        time: Date.now() / 1000,
        isSelf: false
      })
    }
  } else {
    // 新增 AI 消息
    messages.value.push({
      content,
      time: Date.now() / 1000,
      isSelf: false
    })
  }
  scrollToBottom()
}

// ========== 工具方法 ==========
const formatTime = (timestamp: number) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

const formatMessageTime = (timestamp: number) => {
  return dayjs.unix(timestamp).format('HH:mm:ss')
}

// ========== 文档预览 ==========
const previewVisible = ref(false)
const previewTitle = ref('')
const previewContent = ref('')
const previewLoading = ref(false)

const handleSourceClick = async (docId: string, filename: string) => {
  previewTitle.value = `文档预览 - ${filename}`
  previewVisible.value = true
  previewLoading.value = true
  previewContent.value = ''

  try {
    const res = await getKnowledgeFileContent(docId)
    if (res.code === 200 && res.data) {
      previewContent.value = res.data.content
    } else {
      previewContent.value = '加载失败'
    }
  } catch {
    previewContent.value = '加载失败，请稍后重试'
  } finally {
    previewLoading.value = false
  }
}

/**
 * 渲染消息内容
 *
 * 将 [参考X - 来源: xxx 位置|doc_id:yyy] 模式渲染为可点击链接
 */
const renderMessage = (content: string) => {
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  html = html.replace(/\n/g, '<br>')
  // 匹配来源标注: [参考X - 来源: 文件名 位置|doc_id:xxx]
  html = html.replace(
    /\[参考\d+ - 来源: ([^\]|]+?)(?:\s+([^\]|]+))?\|doc_id:([a-fA-F0-9]+)\]/g,
    (_match, filename: string, location: string, docId: string) => {
      const loc = location ? ` ${location.trim()}` : ''
      // 转义属性值中的特殊字符防止 XSS
      const safeFilename = filename.trim().replace(/"/g, '&quot;').replace(/'/g, '&#39;')
      const safeDocId = docId.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
      const label = `${filename.trim()}${loc}`
      return `<span class="source-link" data-doc-id="${safeDocId}" data-filename="${safeFilename}">${label}</span>`
    }
  )
  return html
}

// 事件委托：在消息列表容器上监听点击，避免全局污染
const handleMessageClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (target.classList.contains('source-link')) {
    const docId = target.getAttribute('data-doc-id')
    const filename = target.getAttribute('data-filename')
    if (docId && filename) {
      handleSourceClick(docId, filename)
    }
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.knowledge-page {
  height: calc(100vh - 140px);
}

.knowledge-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.knowledge-container :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-content {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  padding: 30px 20px;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.file-list {
  margin-top: 20px;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
  color: #303133;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
  transition: all 0.2s;
}

.file-item:hover {
  background-color: #ecf5ff;
}

.file-info {
  flex: 1;
  overflow: hidden;
}

.file-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.tips-card {
  margin-top: auto;
}

.tips-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.tips-content p {
  margin: 8px 0;
}

.chat-section {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.message-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f7fa;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.self {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-item.self .message-content {
  align-items: flex-end;
}

.message-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #909399;
}

.message-item.self .message-meta {
  flex-direction: row-reverse;
}

.message-bubble {
  background-color: #ffffff;
  padding: 12px 16px;
  border-radius: 8px;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.message-item.self .message-bubble {
  background-color: #409eff;
  color: #ffffff;
}

.text-message {
  line-height: 1.6;
  white-space: pre-wrap;
}

.tool-call-bar {
  display: flex;
  gap: 12px;
  padding: 8px 16px;
  background-color: #fafafa;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
}

.tool-call-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.message-input-area {
  flex-shrink: 0;
  border-top: 1px solid #dcdfe6;
  padding: 16px;
  background-color: #ffffff;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-box :deep(.el-textarea) {
  flex: 1;
}

@media (max-width: 1200px) {
  .knowledge-content {
    grid-template-columns: 300px 1fr;
  }
}

@media (max-width: 768px) {
  .knowledge-content {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .upload-section {
    max-height: 400px;
  }
}

/* 来源标注可点击样式 */
.source-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
  font-weight: 500;
}

.source-link:hover {
  color: #66b1ff;
}

/* 文档预览弹窗 */
.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
}

.preview-content {
  max-height: 65vh;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}
</style>
