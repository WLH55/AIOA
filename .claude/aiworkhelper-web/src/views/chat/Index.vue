<template>
  <div class="chat-page">
    <el-row :gutter="20" style="height: 100%;">
      <!-- 左侧会话列表 -->
      <el-col :xs="24" :sm="8" :md="6" style="height: 100%;">
        <el-card class="chat-sidebar" body-style="padding: 0;">
          <template #header>
            <div class="sidebar-header">
              <span>消息</span>
              <el-dropdown @command="handleMenuCommand">
                <el-button circle size="small">
                  <el-icon><Plus /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="ai">AI对话</el-dropdown-item>
                    <el-dropdown-item command="group">群聊</el-dropdown-item>
                    <el-dropdown-item command="private">发起私聊</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <div class="conversation-list">
            <!-- AI助手 -->
            <div
              :class="['conversation-item', { active: activeConversation === 'ai' }]"
              @click="switchConversation(conversations[0])"
            >
              <el-avatar :size="40" style="background-color: #409eff;">AI</el-avatar>
              <div class="conversation-info">
                <div class="conversation-name">AI助手</div>
                <div class="conversation-last">你好，我是AI助手</div>
              </div>
            </div>

            <!-- 群聊列表 -->
            <div
              v-for="conv in groupConversations"
              :key="conv.id"
              :class="['conversation-item', { active: activeConversation === conv.id }]"
              @click="switchConversation(conv)"
            >
              <el-avatar :size="40" style="background-color: #67c23a;">群</el-avatar>
              <div class="conversation-info">
                <div class="conversation-name">{{ conv.name }}</div>
                <div class="conversation-last">{{ conv.lastMessage || '暂无消息' }}</div>
              </div>
              <!-- 未读消息徽章 -->
              <el-badge
                v-if="getUnreadCount(conv.id) > 0"
                :value="getUnreadCount(conv.id)"
                :max="99"
                class="unread-badge"
              />
            </div>

            <!-- 已有私聊会话列表（按最新消息时间排序） -->
            <div
              v-for="conv in sortedPrivateConversations"
              :key="conv.id"
              :class="['conversation-item', {
                active: activeConversation === conv.id
              }]"
              @click="switchConversation(conv)"
            >
              <el-avatar :size="40">{{ conv.name[0] }}</el-avatar>
              <div class="conversation-info">
                <div class="conversation-name">{{ conv.name }}</div>
                <div class="conversation-last">
                  {{ conv.lastMessage || '暂无消息' }}
                </div>
              </div>
              <!-- 未读消息徽章 -->
              <el-badge
                v-if="getUnreadCount(conv.id) > 0"
                :value="getUnreadCount(conv.id)"
                :max="99"
                class="unread-badge"
              />
            </div>

            <!-- 没有会话的其他用户 -->
            <div
              v-for="user in usersWithoutConversation"
              :key="user.id"
              :class="['conversation-item', {
                active: isUserInActivePrivateChat(user.id)
              }]"
              @click="startPrivateChatWithUser(user)"
            >
              <el-avatar :size="40">{{ user.name[0] }}</el-avatar>
              <div class="conversation-info">
                <div class="conversation-name">{{ user.name }}</div>
                <div class="conversation-last">点击开始聊天</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧聊天区域 -->
      <el-col :xs="24" :sm="16" :md="18" style="height: 100%;">
        <el-card class="chat-main">
          <template #header>
            <div class="chat-header">
              <span>{{ currentConversationName }}</span>
              <div class="header-actions">
                <el-tag v-if="wsConnected" type="success" size="small">已连接</el-tag>
                <el-tag v-else type="danger" size="small">未连接</el-tag>
                <!-- 群聊设置按钮 -->
                <el-button
                  v-if="currentChatType === 'group'"
                  type="primary"
                  size="small"
                  link
                  @click="openGroupManage"
                >
                  群设置
                </el-button>
              </div>
            </div>
          </template>

          <div class="chat-container">
            <!-- 消息列表 -->
            <div ref="messageListRef" class="message-list">
              <div
                v-for="(msg, index) in sortedMessages"
                :key="index"
                :class="['message-item', msg.isSelf ? 'self' : 'other']"
              >
                <el-avatar :size="36">
                  {{ msg.senderName?.[0] || 'U' }}
                </el-avatar>
                <div class="message-content">
                  <div class="message-meta">
                    <span class="sender-name">{{ msg.senderName }}</span>
                    <span class="message-time">{{ formatTime(msg.time) }}</span>
                  </div>
                  <div class="message-bubble">
                    <div v-if="msg.contentType === 1" class="text-message">
                      {{ msg.content }}
                    </div>
                    <img v-else-if="msg.contentType === 2" :src="msg.content" class="image-message" />
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

            <!-- 输入区域 -->
            <div class="message-input-area">
              <div class="input-box" style="position: relative;">
                <el-input
                  ref="inputRef"
                  v-model="inputMessage"
                  type="textarea"
                  :rows="3"
                  :placeholder="currentChatType === 'group' ? '输入 @ 可提及群成员或AI...' : '请输入消息...'"
                  @keydown.enter.ctrl="handleSend"
                  @input="handleInputChange"
                  @keydown="handleKeyDown"
                />

                <!-- @ 提及选择器 -->
                <div
                  v-if="showMentionList && currentChatType === 'group'"
                  class="mention-list"
                  :style="{ bottom: mentionListBottom + 'px' }"
                >
                  <div
                    v-for="(item, index) in mentionFilteredList"
                    :key="item.id"
                    :class="['mention-item', { active: mentionSelectedIndex === index }]"
                    @click="selectMention(item)"
                    @mouseenter="mentionSelectedIndex = index"
                  >
                    <el-avatar :size="32">{{ item.name[0] }}</el-avatar>
                    <span class="mention-name">{{ item.name }}</span>
                  </div>
                  <div v-if="mentionFilteredList.length === 0" class="mention-empty">
                    无匹配结果
                  </div>
                </div>

                <el-button
                  type="primary"
                  :loading="sending"
                  @click="handleSend"
                >
                  发送 (Ctrl+Enter)
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户选择对话框 -->
    <el-dialog
      v-model="userSelectDialogVisible"
      :title="isCreatingGroup ? '创建群聊 - 选择成员' : '选择用户'"
      width="500px"
    >
      <el-input
        v-model="userSearchKeyword"
        placeholder="搜索用户"
        prefix-icon="Search"
        style="margin-bottom: 16px;"
      />

      <!-- 已选择的用户（创建群聊时显示） -->
      <div v-if="isCreatingGroup && selectedUserIds.length > 0" class="selected-users">
        <el-tag
          v-for="userId in selectedUserIds"
          :key="userId"
          closable
          @close="toggleUserSelection(userId)"
          style="margin-right: 8px; margin-bottom: 8px;"
        >
          {{ userList.find(u => u.id === userId)?.name }}
        </el-tag>
      </div>

      <div class="user-list">
        <div
          v-for="user in filteredUsers"
          :key="user.id"
          :class="['user-item', { selected: selectedUserIds.includes(user.id) }]"
          @click="handleUserSelect(user)"
        >
          <el-avatar :size="36">{{ user.name[0] }}</el-avatar>
          <span class="user-name">{{ user.name }}</span>
          <el-icon v-if="isCreatingGroup && selectedUserIds.includes(user.id)" class="check-icon">
            <el-icon-check />
          </el-icon>
        </div>
      </div>
      <div v-if="filteredUsers.length === 0" class="empty-text">
        暂无用户
      </div>

      <template #footer v-if="isCreatingGroup">
        <el-button @click="userSelectDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedUserIds.length < 2"
          @click="createGroupChat"
        >
          创建群聊 ({{ selectedUserIds.length }}人)
        </el-button>
      </template>
    </el-dialog>

    <!-- 群聊管理对话框 -->
    <el-dialog
      v-model="groupManageVisible"
      title="群聊设置"
      width="500px"
    >
      <div v-if="currentGroupInfo" class="group-manage-content">
        <!-- 群信息 -->
        <div class="group-info-section">
          <h4>群信息</h4>
          <p><strong>群名称：</strong>{{ currentGroupInfo.name }}</p>
          <p><strong>成员数：</strong>{{ currentGroupInfo.memberCount }}人</p>
          <p><strong>群主：</strong>{{ currentGroupInfo.ownerName }}</p>
        </div>

        <!-- 群成员列表 -->
        <div class="group-members-section">
          <h4>群成员</h4>
          <div class="member-list">
            <div
              v-for="member in groupMembers"
              :key="member.id"
              class="member-item"
            >
              <el-avatar :size="32">{{ member.name?.[0] || 'U' }}</el-avatar>
              <span class="member-name">{{ member.name }}</span>
              <el-tag v-if="member.id === currentGroupInfo.ownerId" size="small" type="warning">群主</el-tag>
              <el-button
                v-if="isGroupOwner && member.id !== userStore.userInfo?.id && member.id !== currentGroupInfo.ownerId"
                type="danger"
                size="small"
                link
                @click="handleRemoveMember(member.id, member.name)"
              >
                移出
              </el-button>
            </div>
          </div>
        </div>

        <!-- 群主操作 -->
        <div v-if="isGroupOwner" class="group-actions-section">
          <h4>群主操作</h4>
          <el-button type="primary" @click="openInviteDialog">邀请成员</el-button>
          <el-button type="danger" @click="handleDismissGroup">解散群聊</el-button>
        </div>

        <!-- 普通成员操作 -->
        <div v-else class="group-actions-section">
          <h4>操作</h4>
          <el-button type="warning" @click="handleExitGroup">退出群聊</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="groupManageVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 邀请成员对话框 -->
    <el-dialog
      v-model="inviteDialogVisible"
      title="邀请成员"
      width="400px"
    >
      <div class="invite-content">
        <el-input
          v-model="inviteSearchKeyword"
          placeholder="搜索用户"
          clearable
          style="margin-bottom: 15px;"
        />
        <div class="user-list">
          <div
            v-for="user in filteredInviteUsers"
            :key="user.id"
            :class="['user-item', { selected: inviteSelectedIds.includes(user.id) }]"
            @click="toggleInviteUser(user.id)"
          >
            <el-avatar :size="32">{{ user.name?.[0] || 'U' }}</el-avatar>
            <span class="user-name">{{ user.name }}</span>
            <el-icon v-if="inviteSelectedIds.includes(user.id)" class="check-icon">
              <Check />
            </el-icon>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="inviteDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="inviteSelectedIds.length === 0"
          @click="handleInviteMembers"
        >
          邀请 ({{ inviteSelectedIds.length }}人)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture, Loading, Check } from '@element-plus/icons-vue'
import { chat, createGroup, getChatHistory, getGroupList, getGroupInfo, inviteGroupMembers, removeGroupMember, exitGroup, updateGroup, dismissGroup, getUnreadList, clearUnread } from '@/api/chat'
import { uploadFile } from '@/api/upload'
import { getUserList } from '@/api/user'
import { getWebSocket, releaseWebSocket, WebSocketClient } from '@/utils/websocket'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'
import type { WsMessage, User } from '@/types'

const userStore = useUserStore()

/**
 * 生成私聊会话ID（与后端保持一致）
 * 规则：private_{min(userId1, userId2)}_{max(userId1, userId2)}
 */
const generatePrivateConversationId = (userId1: string, userId2: string): string => {
  const sortedIds = [userId1, userId2].sort()
  return `private_${sortedIds[0]}_${sortedIds[1]}`
}

interface Message {
  sendId: string
  senderName: string
  content: string
  contentType: number
  time: number
  isSelf: boolean
}

interface Conversation {
  id: string
  name: string
  type: 'ai' | 'group' | 'private'
  lastMessage: string
  memberIds?: string[] // 群聊成员ID列表
  creatorId?: string   // 群创建者ID
  createTime?: number  // 创建时间
  conversationId?: string  // 服务端返回的真实会话ID（用于查询历史消息）
}

const messageListRef = ref<HTMLElement>()
const inputRef = ref()
const messages = ref<Message[]>([])
const inputMessage = ref('')
const sending = ref(false)
const aiLoading = ref(false)

// 未读消息计数状态
const unreadCounts = reactive<Record<string, number>>({})

// 群聊管理相关状态
const groupManageVisible = ref(false)
const currentGroupInfo = ref<any>(null)
const groupMembers = ref<User[]>([])

// 邀请成员相关
const inviteDialogVisible = ref(false)
const inviteSearchKeyword = ref('')
const inviteSelectedIds = ref<string[]>([])

// 计算属性：当前用户是否是群主
const isGroupOwner = computed(() => {
  return currentGroupInfo.value?.ownerId === userStore.userInfo?.id
})

// 计算属性：可邀请的用户列表（排除已在群内的）
const filteredInviteUsers = computed(() => {
  const currentMemberIds = currentGroupInfo.value?.memberIds || []
  return userList.value.filter(u =>
    u.id !== userStore.userInfo?.id &&
    !currentMemberIds.includes(u.id) &&
    u.name?.toLowerCase().includes(inviteSearchKeyword.value.toLowerCase())
  )
})

// @ 提及功能相关
const showMentionList = ref(false)
const mentionSearchText = ref('')
const mentionSelectedIndex = ref(0)
const mentionListBottom = ref(100) // 选择器距离底部的距离

interface MentionItem {
  id: string
  name: string
  type: 'user' | 'ai'
}

// 用户列表相关
const userList = ref<User[]>([])
const userSelectDialogVisible = ref(false)
const userSearchKeyword = ref('')
const selectedUserIds = ref<string[]>([]) // 多选用户ID列表
const isCreatingGroup = ref(false) // 是否正在创建群聊

// WebSocket相关
let wsClient: WebSocketClient | null = null
const wsConnected = ref(false)
// 保存消息处理器的引用，用于清理
let messageHandler: ((message: WsMessage) => void) | null = null

// 会话消息存储（每个会话保存自己的消息）
const conversationMessages = reactive<Record<string, Message[]>>({})

// 会话管理
const conversations = ref<Conversation[]>([
  {
    id: 'ai',
    name: 'AI助手',
    type: 'ai',
    lastMessage: '你好，我是AI助手'
  }
  // 群聊会话将动态添加
])

const activeConversation = ref('ai')
const currentChatType = ref<'ai' | 'group' | 'private'>('ai')
const aiChatType = ref(0)

const currentConversationName = computed(() => {
  return conversations.value.find(c => c.id === activeConversation.value)?.name || ''
})

// 获取群聊列表
const groupConversations = computed(() => {
  return conversations.value.filter(c => c.type === 'group')
})

// 获取私聊会话列表（按最后消息时间排序）
const sortedPrivateConversations = computed(() => {
  const privateConvs = conversations.value.filter(c => c.type === 'private')

  // 按最后消息时间排序（最新的在前面）
  return [...privateConvs].sort((a, b) => {
    const aMessages = conversationMessages[a.id] || []
    const bMessages = conversationMessages[b.id] || []
    const aLastTime = aMessages.length > 0 ? aMessages[aMessages.length - 1].time : 0
    const bLastTime = bMessages.length > 0 ? bMessages[bMessages.length - 1].time : 0
    return bLastTime - aLastTime
  })
})

// 获取私聊会话中的对方用户ID
const getPrivateChatUserId = (conv: Conversation) => {
  if (conv.memberIds && conv.memberIds.length > 0) {
    // 返回不是当前用户的ID
    return conv.memberIds.find(id => id !== userStore.userInfo?.id) || ''
  }
  return ''
}

// 检查用户是否在当前活跃的私聊会话中
const isUserInActivePrivateChat = (userId: string) => {
  if (!activeConversation.value) return false
  
  const activeConv = conversations.value.find(c => c.id === activeConversation.value)
  if (!activeConv || activeConv.type !== 'private') return false
  
  return activeConv.memberIds?.includes(userId) || false
}

// 没有私聊会话的用户列表
const usersWithoutConversation = computed(() => {
  // 获取所有私聊会话中的用户ID
  const privateConvUserIds = new Set<string>()
  
  conversations.value
    .filter(c => c.type === 'private')
    .forEach(conv => {
      // 从 memberIds 中获取对方用户ID（排除自己）
      if (conv.memberIds) {
        conv.memberIds.forEach(id => {
          if (id !== userStore.userInfo?.id) {
            privateConvUserIds.add(id)
          }
        })
      }
    })

  return userList.value.filter(u =>
    u.id !== userStore.userInfo?.id && !privateConvUserIds.has(u.id)
  )
})

// 按时间排序的消息列表
const sortedMessages = computed(() => {
  return [...messages.value].sort((a, b) => a.time - b.time)
})

// 过滤用户列表（对话框用）
const filteredUsers = computed(() => {
  if (!userSearchKeyword.value) {
    return userList.value.filter(u => u.id !== userStore.userInfo?.id)
  }
  return userList.value.filter(
    u => u.id !== userStore.userInfo?.id && u.name.includes(userSearchKeyword.value)
  )
})

// @ 提及候选列表
const mentionCandidates = computed<MentionItem[]>(() => {
  const candidates: MentionItem[] = []

  // 添加 AI 助手
  candidates.push({
    id: 'ai',
    name: 'AI助手',
    type: 'ai'
  })

  // 添加群成员
  const currentConv = conversations.value.find(c => c.id === activeConversation.value)
  if (currentConv && currentConv.type === 'group' && currentConv.memberIds) {
    currentConv.memberIds.forEach(memberId => {
      if (memberId !== userStore.userInfo?.id) {
        const user = userList.value.find(u => u.id === memberId)
        if (user) {
          candidates.push({
            id: user.id,
            name: user.name,
            type: 'user'
          })
        }
      }
    })
  }

  return candidates
})

// 根据搜索文本过滤 @ 提及列表
const mentionFilteredList = computed(() => {
  if (!mentionSearchText.value) {
    return mentionCandidates.value
  }
  return mentionCandidates.value.filter(item =>
    item.name.toLowerCase().includes(mentionSearchText.value.toLowerCase())
  )
})

// 判断用户是否在线（通过账户状态判断）
const isUserOnline = (userId: string) => {
  // 当前登录用户始终在线
  if (userId === userStore.userInfo?.id) {
    return true
  }
  // 查找用户信息，status=1 表示账户启用（在线），status=0 表示禁用（离线）
  const user = userList.value.find(u => u.id === userId)
  return user ? user.status === 1 : false
}

// 点击用户列表中的用户创建私聊
const startPrivateChatWithUser = (user: User) => {
  // 不能和自己聊天
  if (user.id === userStore.userInfo?.id) {
    ElMessage.warning('不能和自己聊天')
    return
  }
  startPrivateChat(user)
}

const formatTime = (timestamp: number) => {
  return dayjs.unix(timestamp).format('HH:mm:ss')
}

// 处理输入变化，检测 @ 符号
const handleInputChange = () => {
  const text = inputMessage.value
  const cursorPos = inputRef.value?.$refs?.textarea?.selectionStart || text.length

  // 查找最近的 @ 符号位置
  let atPos = -1
  for (let i = cursorPos - 1; i >= 0; i--) {
    if (text[i] === '@') {
      atPos = i
      break
    }
    if (text[i] === ' ' || text[i] === '\n') {
      break
    }
  }

  if (atPos !== -1 && currentChatType.value === 'group') {
    // 提取 @ 后的搜索文本
    const searchText = text.substring(atPos + 1, cursorPos)
    mentionSearchText.value = searchText
    showMentionList.value = true
    mentionSelectedIndex.value = 0
  } else {
    showMentionList.value = false
    mentionSearchText.value = ''
  }
}

// 处理键盘事件（上下箭头选择，回车确认）
const handleKeyDown = (event: KeyboardEvent) => {
  if (!showMentionList.value) return

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    mentionSelectedIndex.value = Math.min(
      mentionSelectedIndex.value + 1,
      mentionFilteredList.value.length - 1
    )
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    mentionSelectedIndex.value = Math.max(mentionSelectedIndex.value - 1, 0)
  } else if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey) {
    event.preventDefault()
    if (mentionFilteredList.value[mentionSelectedIndex.value]) {
      selectMention(mentionFilteredList.value[mentionSelectedIndex.value])
    }
  } else if (event.key === 'Escape') {
    showMentionList.value = false
  }
}

// 选择提及的用户或AI
const selectMention = (item: MentionItem) => {
  const text = inputMessage.value
  const cursorPos = inputRef.value?.$refs?.textarea?.selectionStart || text.length

  // 查找最近的 @ 符号位置
  let atPos = -1
  for (let i = cursorPos - 1; i >= 0; i--) {
    if (text[i] === '@') {
      atPos = i
      break
    }
  }

  if (atPos !== -1) {
    // 替换 @ 后的文本为选中的名称
    const before = text.substring(0, atPos)
    const after = text.substring(cursorPos)
    inputMessage.value = before + '@' + item.name + ' ' + after

    // 隐藏选择列表
    showMentionList.value = false
    mentionSearchText.value = ''

    // 重新聚焦输入框
    nextTick(() => {
      const textarea = inputRef.value?.$refs?.textarea
      if (textarea) {
        textarea.focus()
        const newPos = (before + '@' + item.name + ' ').length
        textarea.setSelectionRange(newPos, newPos)
      }
    })
  }
}

// 初始化WebSocket连接
const initWebSocket = async () => {
  if (!userStore.token) return

  try {
    // 使用全局单例获取 WebSocket 客户端
    console.log('[WebSocket] 获取全局单例连接')
    wsClient = getWebSocket(userStore.token)

    // 如果还未连接，则连接
    if (!wsClient.isConnected) {
      console.log('[WebSocket] 开始连接...')
      await wsClient.connect()
      wsConnected.value = true
    } else {
      console.log('[WebSocket] 已连接，复用现有连接')
      wsConnected.value = true
    }

    // 创建并添加消息处理器
    if (!messageHandler) {
      messageHandler = (message: WsMessage) => {
        console.log('[WebSocket] 消息处理器被调用，处理消息:', message)
        handleReceiveMessage(message)
      }
    }

    // 添加消息监听器
    console.log('[WebSocket] 添加消息监听器')
    wsClient.onMessage(messageHandler)

    ElMessage.success('WebSocket连接成功')
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    ElMessage.error('WebSocket连接失败')
  }
}

// 接收消息
const handleReceiveMessage = (wsMessage: WsMessage) => {
  try {
    console.log('[接收消息] 收到WebSocket消息:', wsMessage)

    // 处理系统消息（群聊创建通知等）
    if (wsMessage.chatType === 99) {
    console.log('[接收消息] 收到系统消息:', wsMessage.systemType)

    if (wsMessage.systemType === 'group_create' && wsMessage.groupInfo) {
      const { groupId, groupName, memberIds, creatorId } = wsMessage.groupInfo

      // 检查自己是否在群成员列表中
      const isMyGroup = memberIds.includes(userStore.userInfo?.id || '')

      console.log('[接收消息] 群聊创建通知:', {
        groupId,
        groupName,
        memberIds,
        当前用户ID: userStore.userInfo?.id,
        是否是我的群: isMyGroup
      })

      if (isMyGroup) {
        // 检查本地是否已存在该群聊
        const existingGroup = conversations.value.find(c => c.id === groupId)
        if (!existingGroup) {
          // 创建群聊会话
          const newGroup: Conversation = {
            id: groupId,
            name: groupName,
            type: 'group',
            lastMessage: wsMessage.content,
            memberIds,
            creatorId,
            createTime: Date.now()
          }
          conversations.value.push(newGroup)
          console.log('[接收消息] 自动创建群聊会话:', newGroup)

          // 如果不是创建者，显示通知
          if (creatorId !== userStore.userInfo?.id) {
            ElMessage.success(`你已被邀请加入群聊"${groupName}"`)
          }
        }
      }
    }
    return // 系统消息不需要显示在聊天列表中
  }

  // 获取发送者名称
  const senderUser = userList.value.find(u => u.id === wsMessage.sendId)
  let senderName: string
  if (wsMessage.sendId === userStore.userInfo?.id) {
    senderName = '我'
  } else if (wsMessage.sendId === 'ai') {
    senderName = 'AI助手'
  } else if (senderUser) {
    senderName = senderUser.name
  } else {
    senderName = '用户' + (wsMessage.sendId?.slice(0, 4) || 'unknown')
  }

  const message: Message = {
    sendId: wsMessage.sendId,
    senderName,
    content: wsMessage.content,
    contentType: wsMessage.contentType,
    time: Date.now() / 1000,
    isSelf: wsMessage.sendId === userStore.userInfo?.id
  }

  console.log('[接收消息] 转换后的消息对象:', message)

  // 根据消息类型添加到对应会话
  if (wsMessage.chatType === 1) {
    // 群聊消息
    const convId = wsMessage.conversationId

    // 检查是否是自己所在的群
    let groupConv = conversations.value.find(c => c.id === convId && c.type === 'group')

    console.log('[接收消息] 群聊消息处理:', {
      conversationId: convId,
      找到群会话: !!groupConv,
      当前会话: activeConversation.value,
      消息内容: message.content,
      发送者ID: wsMessage.sendId,
      当前用户ID: userStore.userInfo?.id
    })

    // 如果本地没有这个群聊会话，自动创建该群聊
    // 无论是自己发的还是别人发的，只要收到消息就说明这个群是存在的
    if (!groupConv) {
      console.log('[接收消息] 收到未知群的消息，自动创建群聊会话')

      // 尝试从消息内容中提取群名称（如果是创建群聊的欢迎消息）
      let groupName = convId // 默认使用群ID
      const createPattern = /创建了群聊"(.+?)"，成员：(.+)/
      const match = message.content.match(createPattern)
      if (match) {
        groupName = match[1] // 提取群名称
        console.log('[接收消息] 从消息中提取群名称:', groupName)
      } else {
        // 如果无法提取，使用发送者名称
        const senderName = senderUser?.name || '未知用户'
        groupName = `${senderName}的群聊`
      }

      groupConv = {
        id: convId,
        name: groupName,
        type: 'group',
        lastMessage: '',
        memberIds: [userStore.userInfo?.id || '', wsMessage.sendId], // 至少包含自己和发送者
        creatorId: wsMessage.sendId,
        createTime: Date.now()
      }
      conversations.value.push(groupConv)

      // 只有不是自己发的消息才提示加入群聊
      if (wsMessage.sendId !== userStore.userInfo?.id) {
        ElMessage.success(`你已加入群聊"${groupConv.name}"`)
      }
    }

    if (!conversationMessages[convId]) {
      conversationMessages[convId] = []
    }

    // 去重检查：群聊消息去重
    // 检查conversationMessages中是否已有相同的消息
    const existsInStorage = conversationMessages[convId].some(m =>
      m.sendId === message.sendId &&
      m.content === message.content &&
      m.contentType === message.contentType &&
      Math.abs(m.time - message.time) < 5
    )

    console.log('[接收消息-群聊] 去重检查:', {
      conversationId: convId,
      存储中消息数: conversationMessages[convId].length,
      是否已存在: existsInStorage,
      消息详情: { sendId: message.sendId, content: message.content.substring(0, 30), time: message.time }
    })

    if (existsInStorage) {
      console.log('[接收消息-群聊] 检测到重复消息（存储中已存在），跳过添加')
      return
    }

    // 添加到会话消息存储
    conversationMessages[convId].push(message)
    console.log('[接收消息-群聊] 消息已添加到存储，当前存储消息数:', conversationMessages[convId].length)

    // 更新会话列表的最后一条消息
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.lastMessage = message.contentType === 1 ? message.content : '[图片]'
    }
    // 如果当前不在该会话，增加未读计数
    if (activeConversation.value !== convId) {
      incrementUnreadCount(convId, 1)
      console.log('[接收消息-群聊] 不在当前会话，增加未读计数')
    }



    // 如果当前在该会话，更新显示列���并滚动
    if (activeConversation.value === convId) {
      // 再次检查显示列表中是否已存在（双重保险）
      const existsInDisplay = messages.value.some(m =>
        m.sendId === message.sendId &&
        m.content === message.content &&
        m.contentType === message.contentType &&
        Math.abs(m.time - message.time) < 5
      )

      if (existsInDisplay) {
        console.log('[接收消息-群聊] 检测到重复消息（显示列表中已存在），跳过显示')
        return
      }

      console.log('[接收消息-群聊] 添加消息到显示列表')
      console.log('[接收消息-群聊] 添加前messages.value长度:', messages.value.length)
      messages.value.push(message)
      console.log('[接收消息-群聊] 添加后messages.value长度:', messages.value.length)
      scrollToBottom()
    } else {
      console.log('[接收消息-群聊] 不在当前会话，消息已保存但不显示')
    }
  } else if (wsMessage.chatType === 2) {
    // 私聊消息处理
    // 确定对话的另一方用户ID（用于显示头像和名称）
    const otherUserId = wsMessage.sendId === userStore.userInfo?.id ? wsMessage.recvId : wsMessage.sendId

    console.log('[接收消息-私聊] 收到私聊消息:', {
      后端conversationId: wsMessage.conversationId,
      sendId: wsMessage.sendId,
      recvId: wsMessage.recvId,
      当前用户ID: userStore.userInfo?.id,
      对方用户ID: otherUserId,
      消息内容: wsMessage.content,
      是自己发的: wsMessage.sendId === userStore.userInfo?.id
    })

    // 关键修复：使用对方用户ID作为存储键，而不是后端的conversationId
    // 这样可以确保与同一个人的所有消息都存储在同一个地方
    const storageKey = `private_${otherUserId}`

    if (!conversationMessages[storageKey]) {
      conversationMessages[storageKey] = []
    }

    console.log('[接收消息-私聊] 使用存储键:', storageKey)

    // 查找或创建私聊会话
    // 使用 memberIds 来查找会话（而不是会话ID）
    console.log('[接收消息-私聊] 查找私聊会话:', {
      对方用户ID: otherUserId,
      当前用户ID: userStore.userInfo?.id,
      所有会话: conversations.value.map(c => ({ id: c.id, type: c.type, memberIds: c.memberIds, conversationId: c.conversationId }))
    })

    let conv = conversations.value.find(c =>
      c.type === 'private' &&
      c.memberIds?.includes(otherUserId) &&
      c.memberIds?.includes(userStore.userInfo?.id || '')
    )

    console.log('[接收消息-私聊] 查找结果:', {
      找到会话: !!conv,
      会话详情: conv ? JSON.parse(JSON.stringify(conv)) : null
    })

    // 先更新会话的 conversationId（无论消息来自谁，无论是否重复）
    if (wsMessage.conversationId) {
      console.log('[接收消息-私聊] 准备更新 conversationId:', {
        服务端返回的ID: wsMessage.conversationId,
        当前会话是否存在: !!conv,
        会话当前的ID: conv?.conversationId
      })
      if (!conv) {
        // 如果会话不存在，先创建
        const otherUser = userList.value.find(u => u.id === otherUserId)
        conv = {
          id: storageKey,
          name: otherUser?.name || '用户' + otherUserId.slice(0, 4),
          type: 'private',
          lastMessage: '',
          memberIds: [userStore.userInfo?.id || '', otherUserId],
          conversationId: wsMessage.conversationId
        }
        conversations.value.push(conv)
        console.log('[接收消息-私聊] 创建新的私聊会话:', conv)
      } else {
        // 如果会话存在，更新 conversationId（即使已有也要更新）
        if (conv.conversationId !== wsMessage.conversationId) {
          console.log('[接收消息-私聊] 更新前 conversationId:', conv.conversationId)
          conv.conversationId = wsMessage.conversationId
          console.log('[接收消息-私聊] 更新后 conversationId:', conv.conversationId)
        } else {
          console.log('[接收消息-私聊] conversationId 无需更新，已是最新')
        }
      }
    }

    // 检查重复消息（放在更新 conversationId 之后）
    const recentMessages = conversationMessages[storageKey].slice(-10)
    const isDuplicate = recentMessages.some(m =>
      m.sendId === message.sendId &&
      m.content === message.content &&
      m.contentType === message.contentType &&
      Math.abs(m.time - message.time) < 3
    )

    if (isDuplicate) {
      console.log('[接收消息-私聊] 检测到重复的私聊消息，已忽略')
      // 即使是重复消息，也要更新会话的最后消息
      if (conv) {
        conv.lastMessage = message.contentType === 1 ? message.content : '[图片]'
      }
      return
    }

    // 特殊处理：如果是自己发送的消息回显，且已经通过乐观更新添加过，则跳过
    console.log('[接收消息-私聊] 检查消息发送者ID:', wsMessage.sendId, '当前用户ID:', userStore.userInfo?.id)
    if (wsMessage.sendId === userStore.userInfo?.id) {
      console.log('[接收消息-私聊] 收到自己发送的消息回显，跳过添加（已通过乐观更新处理）')
      return
    }

    // 添加到消息存储
    conversationMessages[storageKey].push(message)
    console.log('[接收消息-私聊] 消息已添加到存储，当前存储消息数:', conversationMessages[storageKey].length)

    // 更新已有会话的最后消息
    if (conv) {
      conv.lastMessage = message.contentType === 1 ? message.content : '[图片]'
      console.log('[接收消息-私聊] 更新已有私聊会话:', conv)
    }

    // 如果当前不在该会话，增加未读计数
    if (activeConversation.value !== conv.id) {
      incrementUnreadCount(conv.id, 1)
      console.log('[接收消息-私聊] 不在当前会话，增加未读计数')
    }


    // 如果当前在该会话，更新消息列表并滚动
    if (activeConversation.value === conv.id) {
      console.log('[接收消息-私聊] 添加消息到当前显示列表')
      console.log('[接收消息-私聊] 添加前messages.value长度:', messages.value.length)
      console.log('[接收消息-私聊] 要添加的消息:', {
        sendId: message.sendId,
        content: message.content,
        time: message.time
      })

      // 检查消息是否已存在（避免WebSocket回显导致的重复）
      const messageExists = messages.value.some(existingMsg =>
        existingMsg.sendId === message.sendId &&
        existingMsg.content === message.content &&
        existingMsg.time === message.time
      )

      if (!messageExists) {
        console.log('[接收消息-私聊] 消息不存在，添加到显示列表')
        messages.value.push(message)
        console.log('[接收消息-私聊] 添加后messages.value长度:', messages.value.length)
        scrollToBottom()
      } else {
        console.log('[接收消息-私聊] 消息已存在，跳过添加（避免重复）')
      }
    } else {
      console.log('[接收消息-私聊] 不在当前会话，私聊消息已保存但不显示')
    }
  }
  } catch (error) {
    console.error('[接收消息-错误] WebSocket消息处理失败:', error)
    console.error('[接收消息-错误] 原始消息:', wsMessage)
  }
}

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim()) return

  if (currentChatType.value === 'ai') {
    // AI对话
    await sendAIMessage()
  } else if (currentChatType.value === 'group') {
    // 群聊 - 检查是否 @AI助手 或 @AI
    const content = inputMessage.value.trim()
    if (content.includes('@AI助手') || content.includes('@AI') || content.includes('@ai')) {
      await sendAIMessageInGroup()
    } else {
      await sendGroupMessage()
    }
  } else if (currentChatType.value === 'private') {
    // 私聊
    await sendPrivateMessage()
  }
}

// 发送AI消息
const sendAIMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content) return

  // 添加用户消息到列表
  messages.value.push({
    sendId: userStore.userInfo?.id || '',
    senderName: '我',
    content,
    contentType: 1,
    time: Date.now() / 1000,
    isSelf: true
  })

  inputMessage.value = ''
  scrollToBottom()

  aiLoading.value = true
  try {
    const res = await chat({
      prompts: content,
      chatType: aiChatType.value
    })

    if (res.code === 200) {
      // 格式化AI回复内容
      let content = ''
      let rawData = res.data.data

      console.log('[AI回复] 原始数据类型:', typeof rawData)
      console.log('[AI回复] 原始数据 (完整):', rawData)
      console.log('[AI回复] 原始数据长度:', typeof rawData === 'string' ? rawData.length : 'N/A')

      // 如果是字符串，尝试提取其中的JSON
      if (typeof rawData === 'string') {
        // 检查是否包含```json代码块（支持```json或```格式）
        const jsonBlockMatch = rawData.match(/```json\s*\n([\s\S]*?)\n```/) ||
                               rawData.match(/```\s*\n([\s\S]*?)\n```/) ||
                               rawData.match(/```json\s*([\s\S]*?)```/) ||
                               rawData.match(/```([\s\S]*?)```/)

        if (jsonBlockMatch) {
          try {
            console.log('[AI回复] 检测到JSON代码块，提取内容')
            const jsonStr = jsonBlockMatch[1].trim()
            rawData = JSON.parse(jsonStr)
            console.log('[AI回复] 成功解析JSON:', rawData)
          } catch (e) {
            console.error('[AI回复] JSON解析失败:', e)
            // 尝试直接解析整个字符串
            try {
              rawData = JSON.parse(rawData)
              console.log('[AI回复] 直接解析原始字符串成功')
            } catch (e2) {
              content = rawData
            }
          }
        } else {
          // 没有代码块，尝试直接解析为JSON
          try {
            const parsed = JSON.parse(rawData)
            rawData = parsed
            console.log('[AI回复] 直接解析字符串为JSON成功')
          } catch (e) {
            // 解析失败，作为普通文本处理
            content = rawData
          }
        }
      }

      // 如果成功解析出对象，进行格式化
      if (content === '' && typeof rawData === 'object' && rawData !== null) {
        // 检查是否是标准的AI响应格式 {chatType: 1, data: {...}}
        if (rawData.chatType !== undefined && rawData.data !== undefined) {
          console.log('[AI回复] 检测到标准AI响应格式, chatType:', rawData.chatType)

          // chatType=1 表示待办查询
          if (rawData.chatType === 1 && rawData.data !== null && rawData.data.count !== undefined) {
            const todos = rawData.data.data || []
            const count = rawData.data.count
            console.log('[AI回复] 待办查询结果，数量:', count)

            if (count === 0 || todos.length === 0) {
              content = '📋 暂无待办事项'
            } else {
              content = `📋 找到 ${count} 个待办事项:\n\n` +
                todos.map((todo: any, index: number) => {
                  const deadline = new Date(todo.deadlineAt * 1000).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  })
                  const statusText = todo.status === 0 ? '📌 未发布' : todo.status === 1 ? '⏳ 进行中' : '✅ 已完成'
                  return `${index + 1}. 【${todo.title}】\n` +
                         `   👤 创建人: ${todo.creatorName}\n` +
                         `   ⏰ 截止: ${deadline}\n` +
                         `   ${statusText}\n` +
                         `   📝 描述: ${todo.desc || '无'}`
                }).join('\n\n')
            }
          }
          // chatType=3 表示审批查询
          else if (rawData.chatType === 3 && rawData.data !== null && rawData.data.count !== undefined) {
            const approvals = rawData.data.data || []
            const count = rawData.data.count
            console.log('[AI回复] 审批查询结果，数量:', count)

            if (count === 0 || approvals.length === 0) {
              content = '📝 暂无审批单'
            } else {
              // 审批类型映射（与后端保持一致: 1=通用, 2=请假, 3=补卡, 4=外出, 5=报销, 6=付款, 7=采购, 8=收款）
              const typeMap: Record<number, string> = {
                1: '通用', 2: '请假', 3: '补卡', 4: '外出',
                5: '报销', 6: '付款', 7: '采购', 8: '收款'
              }
              // 审批状态映射
              const statusMap: Record<number, string> = {
                0: '⏸️ 未开始', 1: '⏳ 进行中',
                2: '✅ 已通过', 3: '🔙 已撤销', 4: '❌ 已拒绝'
              }

              content = `📝 找到 ${count} 个审批单:\n\n` +
                approvals.map((approval: any, index: number) => {
                  const createTime = approval.createAt
                    ? new Date(approval.createAt * 1000).toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })
                    : '无'
                  const typeText = typeMap[approval.type] || '未知'
                  const statusText = statusMap[approval.status] || '未知'

                  // 通过createId查找创建人名称
                  const creator = userList.value.find(u => u.id === approval.createId)
                  const creatorName = creator?.name || approval.creatorId || '未知'

                  return `${index + 1}. 【${approval.title || '无标题'}】\n` +
                         `   📂 类型: ${typeText}\n` +
                         `   👤 创建人: ${creatorName}\n` +
                         `   🕐 创建时间: ${createTime}\n` +
                         `   ${statusText}\n` +
                         `   📄 详情: ${approval.abstract || '无'}`
                }).join('\n\n')
            }
          } else {
            // 其他chatType类型，使用通用格式化
            content = JSON.stringify(rawData.data, null, 2)
          }
        }
        // 检查是否是嵌套结构的待办查询结果（兼容旧格式）
        else if (rawData.data && rawData.data.count !== undefined && Array.isArray(rawData.data.data)) {
          const todos = rawData.data.data
          const count = rawData.data.count
          console.log('[AI回复] 检测到嵌套待办结果，数量:', count)
          if (todos.length === 0) {
            content = '📋 暂无待办事项'
          } else {
            content = `📋 找到 ${count} 个待办事项:\n\n` +
              todos.map((todo: any, index: number) => {
                const deadline = new Date(todo.deadlineAt * 1000).toLocaleString('zh-CN', {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit'
                })
                const statusText = todo.status === 0 ? '📌 未发布' : todo.status === 1 ? '⏳ 进行中' : '✅ 已完成'
                return `${index + 1}. 【${todo.title}】\n` +
                       `   👤 创建人: ${todo.creatorName}\n` +
                       `   ⏰ 截止: ${deadline}\n` +
                       `   ${statusText}\n` +
                       `   📝 描述: ${todo.desc || '无'}`
              }).join('\n\n')
          }
        } else if (Array.isArray(rawData)) {
          // 直接是数组的情况
          const todos = rawData
          console.log('[AI回复] 检测到数组格式，数量:', todos.length)
          if (todos.length === 0) {
            content = '暂无待办事项'
          } else {
            content = `找到 ${todos.length} 个待办事项:\n\n` +
              todos.map((todo: any, index: number) => {
                const deadline = new Date(todo.deadlineAt * 1000).toLocaleString('zh-CN')
                const statusText = todo.status === 0 ? '未发布' : todo.status === 1 ? '进行中' : '已完成'
                return `${index + 1}. ${todo.title}\n   创建人: ${todo.creatorName}\n   截止时间: ${deadline}\n   状态: ${statusText}\n   描述: ${todo.desc || '无'}`
              }).join('\n\n')
          }
        } else {
          // 其他对象类型,使用JSON格式
          console.log('[AI回复] 其他对象类型，使用JSON格式')
          content = JSON.stringify(rawData, null, 2)
        }
      }

      console.log('[AI回复] 最终格式化内容:', content.substring(0, 100))

      // 添加AI回复
      messages.value.push({
        sendId: 'ai',
        senderName: 'AI助手',
        content,
        contentType: 1,
        time: Date.now() / 1000,
        isSelf: false
      })
      scrollToBottom()
    }
  } catch (error) {
    ElMessage.error('AI请求失败')
  } finally {
    aiLoading.value = false
  }
}

// 发送群聊消息
const sendGroupMessage = async () => {
  if (!wsClient || !wsClient.isConnected) {
    ElMessage.warning('WebSocket未连接')
    return
  }

  const content = inputMessage.value.trim()
  if (!content) return

  // 获取当前群聊ID
  const currentGroupId = activeConversation.value

  const wsMessage: WsMessage = {
    type: 'chat',
    conversationId: currentGroupId,
    recvId: '',
    sendId: userStore.userInfo?.id || '',
    chatType: 1, // 群聊
    content,
    contentType: 1
  }

  console.log('[发送群聊] 发送消息:', wsMessage)
  wsClient.send(wsMessage)
  inputMessage.value = ''

  // 注意: 不在这里做乐观更新,等待后端回传消息
  // 这样可以避免消息重复显示的问题
  // 群聊消息后端会回传给所有成员(包括发送者),所以不需要乐观更新
}

// 在群聊中 @AI
const sendAIMessageInGroup = async () => {
  const content = inputMessage.value.trim()
  if (!content) return

  // 获取当前群聊ID
  const currentGroupId = activeConversation.value

  // 移除 @AI助手 或 @AI 前缀
  const prompt = content.replace(/@AI助手\s*/gi, '').replace(/@AI\s*/gi, '')

  // 先发送用户消息到群聊
  if (wsClient && wsClient.isConnected) {
    const wsMessage: WsMessage = {
      type: 'chat',
      conversationId: currentGroupId,
      recvId: '',
      sendId: userStore.userInfo?.id || '',
      chatType: 1,
      content,
      contentType: 1
    }
    wsClient.send(wsMessage)
    console.log('[群聊@AI] 用户消息已发送，等待WebSocket回传确认')
  }

  inputMessage.value = ''

  // 调用 AI 接口进行群消息总结
  aiLoading.value = true
  try {
    // 获取当前时间和24小时前的时间戳（用于总结最近的群消息）
    const now = Date.now()
    const oneDayAgo = now - 24 * 60 * 60 * 1000

    console.log('[群聊@AI] 准备调用API，当前群聊ID:', currentGroupId)

    const res = await chat({
      prompts: prompt,
      chatType: 0,  // 使用默认值0，让后端智能路由自动识别为群消息总结
      relationId: currentGroupId,  // 传递当前群聊的conversationId，后端会查询该群的消息
      startTime: Math.floor(oneDayAgo / 1000),  // 开始时间（秒级时间戳）
      endTime: Math.floor(now / 1000)  // 结束时间（秒级时间戳）
    })

    console.log('[群聊@AI] 后端API响应:', res)

    if (res.code === 200) {
      // 增强数据处理：支持多种返回格式
      let aiResponse = ''

      if (res.data && res.data.data) {
        // 如果返回的是数组（总结结果），格式化展示
        if (Array.isArray(res.data.data)) {
          const summaries = res.data.data.map((item: any, index: number) => {
            const typeLabel = item.Type === 1 ? '📋 待办任务' : '📝 审批事项'
            return `${index + 1}. ${typeLabel}: ${item.Title}\n   ${item.Content}`
          }).join('\n\n')
          aiResponse = summaries || '暂无总结内容'
        } else if (typeof res.data.data === 'string') {
          aiResponse = res.data.data
        } else {
          aiResponse = JSON.stringify(res.data.data, null, 2)
        }
      } else if (res.data && typeof res.data === 'string') {
        aiResponse = res.data
      } else {
        console.warn('[群聊@AI] 后端返回数据格式异常:', res.data)
        aiResponse = '暂无群消息总结'
      }

      console.log('[群聊@AI] 处理后的AI回复:', aiResponse)

      // 将 AI 回复发送到群聊
      if (wsClient && wsClient.isConnected) {
        const wsMessage: WsMessage = {
          type: 'chat',
          conversationId: currentGroupId,
          recvId: '',
          sendId: 'ai',
          chatType: 1,
          content: `AI回复:\n${aiResponse}`,
          contentType: 1
        }
        wsClient.send(wsMessage)
        console.log('[群聊@AI] AI回复已发送到群聊，等待WebSocket回传确认')
      }
    } else {
      console.error('[群聊@AI] 后端返回错误:', res.code, res.msg)
      ElMessage.error(`AI总结失败: ${res.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('[群聊@AI] AI请求失败:', error)
    ElMessage.error('AI请求失败，请检查网络连接')
  } finally {
    aiLoading.value = false
  }
}

// 发送私聊消息
const sendPrivateMessage = async () => {
  if (!wsClient || !wsClient.isConnected) {
    ElMessage.warning('WebSocket未连接')
    return
  }

  const content = inputMessage.value.trim()
  if (!content) return

  // 从当前会话中获取对方用户ID
  const currentConv = conversations.value.find(c => c.id === activeConversation.value)
  if (!currentConv || currentConv.type !== 'private') {
    ElMessage.error('无效的私聊会话')
    return
  }

  console.log('[发送私聊] 当前会话详细信息:', JSON.parse(JSON.stringify(currentConv)))
  console.log('[发送私聊] 当前用户ID:', userStore.userInfo?.id)

  // 从 memberIds 中找到对方的用户ID（排除自己）
  const recvId = currentConv.memberIds?.find(id => id !== userStore.userInfo?.id)
  if (!recvId) {
    console.error('[发送私聊] 无法找到接收者ID:', {
      当前会话: currentConv,
      当前用户ID: userStore.userInfo?.id,
      memberIds: currentConv.memberIds
    })
    ElMessage.error('无法找到接收者ID')
    return
  }

  console.log('[发送私聊] 找到的接收者ID:', recvId)

  // 使用会话中保存的 conversationId，如果没有则动态生成
  const currentUserId = userStore.userInfo?.id || ''
  const conversationIdToUse = currentConv.conversationId || generatePrivateConversationId(currentUserId, recvId)

  // 如果会话没有 conversationId，更新它
  if (!currentConv.conversationId) {
    currentConv.conversationId = conversationIdToUse
    console.log('[发送私聊] 更新会话 conversationId:', conversationIdToUse)
  }

  const wsMessage: WsMessage = {
    type: 'chat',
    conversationId: conversationIdToUse,
    recvId,
    sendId: userStore.userInfo?.id || '',
    chatType: 2,
    content,
    contentType: 1
  }

  console.log('[发送私聊] 发送消息:', {
    conversationId: conversationIdToUse || '(由后端生成)',
    recvId,
    content,
    会话ID: currentConv.id,
    会话conversationId: currentConv.conversationId,
    会话完整对象: JSON.parse(JSON.stringify(currentConv))
  })
  wsClient.send(wsMessage)
  inputMessage.value = ''

  // 立即添加到本地消息列表(乐观更新)
  // 私聊时后端不会回传给发送者，所以必须在本地显示
  const message: Message = {
    sendId: userStore.userInfo?.id || '',
    senderName: '我',
    content,
    contentType: 1,
    time: Date.now() / 1000,
    isSelf: true
  }

  // 关键修复：使用对方用户ID作为会话存储的键，而不是临时会话ID
  // 这样可以确保与同一个人的所有消息都存储在同一个地方
  const storageKey = `private_${recvId}` // 使用统一的存储键格式

  if (!conversationMessages[storageKey]) {
    conversationMessages[storageKey] = []
  }

  console.log('[发送私聊] 使用存储键:', storageKey, '当前会话ID:', activeConversation.value)

  // 去重检查再添加
  const recentMessages = conversationMessages[storageKey].slice(-10)
  const isDuplicate = recentMessages.some(m =>
    m.sendId === message.sendId &&
    m.content === message.content &&
    m.contentType === message.contentType &&
    Math.abs(m.time - message.time) < 3
  )

  if (!isDuplicate) {
    console.log('[发送私聊] 乐观更新：添加到本地消息存储')
    console.log('[发送私聊] 乐观更新消息详情:', {
      sendId: message.sendId,
      content: message.content,
      time: message.time,
      storageKey: storageKey
    })
    conversationMessages[storageKey].push(message)

    // 只有在当前会话中才添加到显示列表
    if (activeConversation.value === currentConv.id) {
      console.log('[发送私聊] 乐观更新：添加到当前显示列表')
      console.log('[发送私聊] 乐观更新前messages.value长度:', messages.value.length)

      // 检查显示列表中是否已存在该消息（避免重复显示）
      const displayMessageExists = messages.value.some(existingMsg =>
        existingMsg.sendId === message.sendId &&
        existingMsg.content === message.content &&
        existingMsg.time === message.time
      )

      if (!displayMessageExists) {
        console.log('[发送私聊] 乐观更新：消息不存在于显示列表，添加')
        messages.value.push(message)
        console.log('[发送私聊] 乐观更新后messages.value长度:', messages.value.length)
        scrollToBottom()
      } else {
        console.log('[发送私聊] 乐观更新：消息已存在于显示列表，跳过添加')
      }
    } else {
      console.log('[发送私聊] 乐观更新：不在当前会话，消息已保存但不显示')
    }
  } else {
    console.log('[发送私聊] 检测到重复消息，跳过乐观更新')
  }
}

// 上传图片
const handleUploadImage = async (file: File) => {
  try {
    const res = await uploadFile(file)
    if (res.code === 200) {
      const imageUrl = `${res.data.host}/${res.data.file}`

      if (currentChatType.value === 'group' && wsClient?.isConnected) {
        // 发送图片消息到群聊
        const wsMessage: WsMessage = {
          type: 'chat',
          conversationId: 'all',
          recvId: '',
          sendId: userStore.userInfo?.id || '',
          chatType: 1,
          content: imageUrl,
          contentType: 2
        }
        wsClient.send(wsMessage)

        messages.value.push({
          sendId: userStore.userInfo?.id || '',
          senderName: '我',
          content: imageUrl,
          contentType: 2,
          time: Date.now() / 1000,
          isSelf: true
        })
        scrollToBottom()
      }
    }
  } catch (error) {
    ElMessage.error('上传失败')
  }

  return false
}

// 切换会话
const switchConversation = async (conv: Conversation) => {
  activeConversation.value = conv.id
  currentChatType.value = conv.type

  // 切换到私聊或群组时，清除未读计数
  if (conv.type === 'private' || conv.type === 'group') {
    await clearConversationUnread(conv.id)
  }

  // 加载该会话的历史消息
  // 先从内存中获取，如果没有则从服务器加载
  if (!conversationMessages[conv.id]) {
    conversationMessages[conv.id] = []
  }
  messages.value = conversationMessages[conv.id] || []

  // 如果内存中没有消息或者是私聊/群聊，从服务器加载历史消息
  if ((conv.type === 'group' || conv.type === 'private') && messages.value.length === 0) {
    // 对于群聊，conv.id 就是服务端的 conversationId
    // 对于私聊，使用 conv.conversationId（服务端返回的）
    const historyConversationId = conv.type === 'group' ? conv.id : conv.conversationId
    console.log('[切换会话] 准备加载历史消息:', {
      会话类型: conv.type,
      客户端会话ID: conv.id,
      服务端会话ID: conv.conversationId,
      将使用的历史ID: historyConversationId
    })
    await loadChatHistory(conv.id, historyConversationId)
  }

  scrollToBottom()

  // 如果切换到群聊或私聊，确保WebSocket已连接
  if ((conv.type === 'group' || conv.type === 'private') && !wsConnected.value) {
    initWebSocket()
  }
}

// 创建私聊会话
const startPrivateChat = (user: User) => {
  userSelectDialogVisible.value = false
  userSearchKeyword.value = ''

  // 检查是否已经存在与该用户的私聊会话
  let conv = conversations.value.find(c =>
    c.type === 'private' &&
    c.memberIds?.includes(user.id) &&
    c.memberIds?.includes(userStore.userInfo?.id || '')
  )

  if (!conv) {
    const currentUserId = userStore.userInfo?.id || ''
    // 生成与服务端一致的 conversationId
    const serverConversationId = generatePrivateConversationId(currentUserId, user.id)
    // 前端会话ID使用简化格式（方便存储和显示）
    const localId = `private_${user.id}`
    conv = {
      id: localId,
      name: user.name,
      type: 'private',
      lastMessage: '',
      memberIds: [currentUserId, user.id],
      conversationId: serverConversationId // 直接使用正确格式，无需等待服务端返回
    }
    conversations.value.push(conv)
    console.log('[创建私聊] 创建会话:', { localId, serverConversationId, conv })
  }

  // 切换到该会话
  switchConversation(conv)
}

// 加载用户列表
const loadUserList = async () => {
  try {
    const res = await getUserList({ page: 1, count: 100 })
    console.log('用户列表接口响应:', res)
    if (res.code === 200) {
      // 处理不同的响应格式
      if (res.data && Array.isArray(res.data)) {
        // 如果 data 直接是数组
        userList.value = res.data
      } else if (res.data && res.data.data && Array.isArray(res.data.data)) {
        // 如果 data.data 是数组
        userList.value = res.data.data
      } else if (res.data === null || res.data === undefined) {
        console.warn('用户列表为空，接口返回 null')
        userList.value = []
      } else {
        console.warn('未知的用户列表响应格式:', res.data)
        userList.value = []
      }
      console.log('加载的用户列表:', userList.value)
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  }
}

// 加载群聊列表
const loadGroupList = async () => {
  try {
    const res = await getGroupList()
    if (res.code === 200 && res.data) {
      const groups = res.data.data || []
      // 将群组转换为会话格式并添加到列表
      groups.forEach((group: any) => {
        // 检查是否已存在
        const exists = conversations.value.find(c => c.id === group.id && c.type === 'group')
        if (!exists) {
          conversations.value.push({
            id: group.id,
            name: group.name,
            type: 'group',
            lastMessage: '',
            memberIds: [], // 成员列表需要单独获取
            creatorId: group.ownerId,
            createTime: group.createAt
          })
        }
      })
      console.log('[加载群聊列表] 加载了', groups.length, '个群聊')
    }
  } catch (error) {
    console.error('[加载群聊列表] 失败:', error)
  }
}

// 处理菜单命令
const handleMenuCommand = (command: string) => {
  if (command === 'ai') {
    switchConversation(conversations.value[0])
  } else if (command === 'group') {
    // 打开创建群聊对话框
    isCreatingGroup.value = true
    selectedUserIds.value = []
    userSearchKeyword.value = ''
    userSelectDialogVisible.value = true
  } else if (command === 'private') {
    // 打开私聊对话框
    isCreatingGroup.value = false
    selectedUserIds.value = []
    userSearchKeyword.value = ''
    userSelectDialogVisible.value = true
  }
}

// 处理用户选择
const handleUserSelect = (user: User) => {
  if (isCreatingGroup.value) {
    // 群聊模式：切换选中状态
    toggleUserSelection(user.id)
  } else {
    // 私聊模式：直接开始私聊
    startPrivateChat(user)
  }
}

// 切换用户选中状态
const toggleUserSelection = (userId: string) => {
  const index = selectedUserIds.value.indexOf(userId)
  if (index > -1) {
    selectedUserIds.value.splice(index, 1)
  } else {
    selectedUserIds.value.push(userId)
  }
}

// 创建群聊
const createGroupChat = async () => {
  if (selectedUserIds.value.length < 2) {
    ElMessage.warning('至少选择2个用户')
    return
  }

  if (!wsClient || !wsClient.isConnected) {
    ElMessage.warning('WebSocket未连接，无法创建群聊')
    return
  }

  // 生成群ID和群名称
  const groupId = `group_${Date.now()}`

  // 获取所有成员（包括创建者自己）的名称
  const allMemberIds = [userStore.userInfo?.id || '', ...selectedUserIds.value]
  const memberNames = allMemberIds
    .map(id => userList.value.find(u => u.id === id)?.name || (id === userStore.userInfo?.id ? userStore.userInfo?.name : ''))
    .filter(Boolean)
    .slice(0, 5) // 最多显示5个名字
  const groupName = memberNames.join('、') + (allMemberIds.length > 5 ? '...' : '')

  console.log('[创建群聊] 准备创建群聊:', {
    groupId,
    groupName,
    memberIds: selectedUserIds.value
  })

  try {
    // 【重要】先调用后端API保存群成员关系
    await createGroup({
      groupId,
      groupName,
      memberIds: selectedUserIds.value // 不包括创建者，后端会自动添加
    })
    console.log('[创建群聊] 后端API调用成功，群成员关系已保存')

    // 然后发送WebSocket欢迎消息
    const welcomeMessage: WsMessage = {
      type: 'chat',
      conversationId: groupId,
      recvId: '',
      sendId: userStore.userInfo?.id || '',
      chatType: 1, // 普通群聊消息
      content: `${userStore.userInfo?.name}创建了群聊"${groupName}"，成员：${memberNames.join('、')}${allMemberIds.length > 5 ? '...' : ''}`,
      contentType: 1
    }

    console.log('[创建群聊] 发送欢迎消息:', welcomeMessage)
    wsClient.send(welcomeMessage)

    // 将新创建的群聊添加到列表中（立即显示）
    const newGroup: Conversation = {
      id: groupId,
      name: groupName,
      type: 'group',
      lastMessage: `${userStore.userInfo?.name}创建了群聊`,
      memberIds: allMemberIds,
      creatorId: userStore.userInfo?.id || '',
      createTime: Date.now()
    }
    conversations.value.push(newGroup)
    console.log('[创建群聊] 已添加到会话列表:', newGroup)

    // 关闭对话框
    userSelectDialogVisible.value = false
    selectedUserIds.value = []

    ElMessage.success(`成功创建群聊"${groupName}"`)
  } catch (error) {
    console.error('[创建群聊] 创建失败:', error)
    ElMessage.error('创建群聊失败，请稍后重试')
  }
}

// ========== 群聊管理相关函数 ==========

/**
 * 打开群聊管理对话框
 */
const openGroupManage = async () => {
  const currentConv = conversations.value.find(c => c.id === activeConversation.value)
  if (!currentConv || currentConv.type !== 'group') return

  try {
    // 获取群组详情
    const res = await getGroupInfo(currentConv.id)
    if (res.code === 200 && res.data) {
      currentGroupInfo.value = res.data

      // 获取群成员详情
      const memberDetails = await Promise.all(
        (res.data.memberIds || []).map(async (memberId: string) => {
          const user = userList.value.find(u => u.id === memberId)
          if (user) return user
          return { id: memberId, name: '用户' + memberId.slice(0, 4) }
        })
      )
      groupMembers.value = memberDetails

      groupManageVisible.value = true
    }
  } catch (error) {
    console.error('[群管理] 获取群信息失败:', error)
    ElMessage.error('获取群信息失败')
  }
}

/**
 * 打开邀请成员对话框
 */
const openInviteDialog = () => {
  inviteSelectedIds.value = []
  inviteSearchKeyword.value = ''
  inviteDialogVisible.value = true
}

/**
 * 切换邀请用户选中状态
 */
const toggleInviteUser = (userId: string) => {
  const index = inviteSelectedIds.value.indexOf(userId)
  if (index > -1) {
    inviteSelectedIds.value.splice(index, 1)
  } else {
    inviteSelectedIds.value.push(userId)
  }
}

/**
 * 邀请成员
 */
const handleInviteMembers = async () => {
  if (!currentGroupInfo.value || inviteSelectedIds.value.length === 0) return

  try {
    const res = await inviteGroupMembers(currentGroupInfo.value.id, inviteSelectedIds.value)
    if (res.code === 200) {
      ElMessage.success('邀请成功')
      inviteDialogVisible.value = false
      await openGroupManage()
    }
  } catch (error) {
    console.error('[群管理] 邀请成员失败:', error)
    ElMessage.error('邀请成员失败')
  }
}

/**
 * 移出群成员
 */
const handleRemoveMember = async (memberId: string, memberName: string) => {
  if (!currentGroupInfo.value) return

  try {
    await ElMessageBox.confirm(`确定要将 ${memberName} 移出群聊吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await removeGroupMember(currentGroupInfo.value.id, memberId)
    if (res.code === 200) {
      ElMessage.success('已移出群聊')
      await openGroupManage()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[群管理] 移出成员失败:', error)
      ElMessage.error('移出成员失败')
    }
  }
}

/**
 * 退出群聊
 */
const handleExitGroup = async () => {
  if (!currentGroupInfo.value) return

  try {
    await ElMessageBox.confirm('确定要退出群聊吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await exitGroup(currentGroupInfo.value.id)
    if (res.code === 200) {
      ElMessage.success('已退出群聊')
      groupManageVisible.value = false
      const index = conversations.value.findIndex(c => c.id === currentGroupInfo.value.id)
      if (index > -1) {
        conversations.value.splice(index, 1)
      }
      switchConversation(conversations.value[0])
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[群管理] 退出群聊失败:', error)
      ElMessage.error('退出群聊失败')
    }
  }
}

/**
 * 解散群聊
 */
const handleDismissGroup = async () => {
  if (!currentGroupInfo.value) return

  try {
    await ElMessageBox.confirm('确定要解散群聊吗？解散后无法恢复！', '警告', {
      confirmButtonText: '确定解散',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await dismissGroup(currentGroupInfo.value.id)
    if (res.code === 200) {
      ElMessage.success('群聊已解散')
      groupManageVisible.value = false
      const index = conversations.value.findIndex(c => c.id === currentGroupInfo.value.id)
      if (index > -1) {
        conversations.value.splice(index, 1)
      }
      switchConversation(conversations.value[0])
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[群管理] 解散群聊失败:', error)
      ElMessage.error('解散群聊失败')
    }
  }
}

// ========== 未读消息相关函数 ==========

/**
 * 获取指定会话的未读数量
 */
const getUnreadCount = (conversationId: string): number => {
  return unreadCounts[conversationId] || 0
}

/**
 * 加载未读消息列表
 */
const loadUnreadList = async () => {
  try {
    const res = await getUnreadList()
    if (res.code === 200 && res.data) {
      res.data.list.forEach(item => {
        unreadCounts[item.conversationId] = item.unreadCount
      })
      console.log('[加载未读] 未读列表加载成功:', res.data.list)
    }
  } catch (error) {
    console.error('[加载未读] 失败:', error)
  }
}

/**
 * 清除会话未读计数
 */
const clearConversationUnread = async (conversationId: string) => {
  if (getUnreadCount(conversationId) > 0) {
    try {
      await clearUnread({ conversationId })
      unreadCounts[conversationId] = 0
      console.log('[清除未读] 会话:', conversationId)
    } catch (error) {
      console.error('[清除未读] 失败:', error)
    }
  }
}

/**
 * 加载会话历史消息
 * @param convId - 客户端会话ID（用于存储）
 * @param historyConversationId - 服务端会话ID（用于查询，可选）
 */
const loadChatHistory = async (convId: string, historyConversationId?: string) => {
  try {
    // 如果没有提供 historyConversationId，尝试从会话对象中获取
    if (!historyConversationId) {
      const conv = conversations.value.find(c => c.id === convId)
      if (conv?.conversationId) {
        historyConversationId = conv.conversationId
      } else if (conv?.type === 'private' && conv.memberIds?.length === 2) {
        // 私聊会话：动态生成与服务端一致的 conversationId
        historyConversationId = generatePrivateConversationId(conv.memberIds[0], conv.memberIds[1])
      } else {
        historyConversationId = convId
      }
    }

    console.log('[加载历史消息] 客户端会话ID:', convId, '服务端会话ID:', historyConversationId)
    const res = await getChatHistory(historyConversationId, 1, 100)
    if (res.code === 200 && res.data && res.data.data) {
      // 将历史消息转换为前端消息格式
      const historyMessages: Message[] = res.data.data.map((msg: any) => ({
        sendId: msg.sendId,
        senderName: msg.sendName || (msg.sendId === userStore.userInfo?.id ? '我' : '用户' + msg.sendId.slice(0, 4)),
        content: msg.msgContent,
        contentType: 1, // 历史消息默认为文字类型
        time: (msg.sendTime || msg.createAt || Date.now()) / 1000,
        isSelf: msg.sendId === userStore.userInfo?.id
      }))

      // 存储到内存中，使用 conv.id 作为键
      conversationMessages[convId] = historyMessages

      // 如果当前正在查看这个会话，更新显示
      if (activeConversation.value === convId) {
        messages.value = historyMessages
        console.log('[加载历史消息] 加载了', historyMessages.length, '条消息')
      }

      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error) {
    console.error('[加载历史消息] 失败:', error)
  }
}

/**
 * 增加会话未读计数（内部使用）
 */
const incrementUnreadCount = (conversationId: string, delta: number = 1) => {
  const current = unreadCounts[conversationId] || 0
  unreadCounts[conversationId] = Math.max(0, current + delta)
  console.log('[增加未读] 会话:', conversationId, '当前未读数:', unreadCounts[conversationId])
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

onMounted(() => {
  // 加载用户列表
  loadUserList()
  // 加载群聊列表
  loadGroupList()
  // 加载未读消息列表
  loadUnreadList()
  // 自动连接 WebSocket
  initWebSocket()
  // 默认显示AI对话
  switchConversation(conversations.value[0])
})

onBeforeUnmount(() => {
  // 只移除消息处理器，不关闭连接（使用全局单例）
  console.log('[组件销毁] 清理WebSocket消息处理器')

  if (wsClient && messageHandler) {
    wsClient.offMessage(messageHandler)
    console.log('[组件销毁] 消息处理器已移除')
  }

  // 释放 WebSocket 引用（引用计数-1，只有计数为0时才真正关闭）
  if (wsClient && userStore.token) {
    releaseWebSocket(userStore.token, wsClient)
    console.log('[组件销毁] WebSocket 引用已释放')
  }

  wsConnected.value = false
  wsClient = null
  messageHandler = null
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 140px);
}

.chat-sidebar,
.chat-main {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-main :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversation-list {
  overflow-y: auto;
  height: calc(100% - 60px);
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px 8px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.user-count {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 12px;
}

.conversation-item:hover {
  background-color: #f5f7fa;
}

.conversation-item.active {
  background-color: #ecf5ff;
  border-left: 3px solid #409eff;
}


.conversation-info {
  flex: 1;
  overflow: hidden;
}

.conversation-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.conversation-last {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-info {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 0;
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
  max-width: 60%;
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
  padding: 10px 14px;
  border-radius: 8px;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.message-item.self .message-bubble {
  background-color: #409eff;
  color: #ffffff;
}

.text-message {
  line-height: 1.5;
  white-space: pre-wrap;
}

.image-message {
  max-width: 300px;
  border-radius: 4px;
}

.message-input-area {
  border-top: 1px solid #dcdfe6;
  padding: 16px;
  background-color: #ffffff;
}

.input-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-box :deep(.el-textarea) {
  flex: 1;
}

/* 用户选择对话框样式 */
.selected-users {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  min-height: 40px;
}

.user-list {
  max-height: 400px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  position: relative;
}

.user-item:hover {
  background-color: #f5f7fa;
}

.user-item.selected {
  background-color: #ecf5ff;
  border-left: 3px solid #409eff;
}

.check-icon {
  margin-left: auto;
  color: #409eff;
  font-size: 18px;
}

.user-name {
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.empty-text {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

/* @ 提及选择器样式 */
.mention-list {
  position: absolute;
  left: 0;
  right: 50px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
}

.mention-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.mention-item:hover,
.mention-item.active {
  background-color: #f5f7fa;
}

.mention-name {
  font-size: 14px;
  color: #303133;
}

.mention-empty {
  padding: 12px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

/* 未读消息徽章样式 */
.unread-badge {
  margin-left: auto;
}

.unread-badge :deep(.el-badge__content) {
  background-color: #F56C6C;
  color: white;
  min-width: 16px;
  height: 16px;
  line-height: 14px;
  font-size: 12px;
  font-weight: bold;
  padding: 1px 6px;
  border-radius: 10px;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 群聊管理样式 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-manage-content {
  padding: 10px 0;
}

.group-info-section,
.group-members-section,
.group-actions-section {
  margin-bottom: 20px;
}

.group-info-section h4,
.group-members-section h4,
.group-actions-section h4 {
  margin-bottom: 10px;
  color: #409eff;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.member-list {
  max-height: 250px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  margin-bottom: 5px;
}

.member-item:hover {
  background-color: #f5f7fa;
}

.member-name {
  flex: 1;
}

.invite-content .user-list {
  max-height: 300px;
  overflow-y: auto;
}

.invite-content .user-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.invite-content .user-item:hover {
  background-color: #f5f7fa;
}

.invite-content .user-item.selected {
  background-color: #ecf5ff;
}

.invite-content .user-name {
  flex: 1;
}
</style>
