import request from '@/utils/request'
import type { ApiResponse, ChatRequest, ChatResponse, GroupListParams, PageData, GroupListItem, GroupInfo, UnreadListResponse, ClearUnreadRequest } from '@/types'
import { useUserStore } from '@/stores/user'

// AI聊天（旧接口，保留兼容）
export function chat(data: ChatRequest): Promise<ApiResponse<ChatResponse>> {
  return request({
    url: '/v1/chat',
    method: 'post',
    data
  })
}


// ==================== AI SSE 流式对话 ====================

/** SSE 事件回调 */
export interface SSECallbacks {
  onChunk?: (content: string, index: number) => void
  onToolCall?: (tool: string, args: Record<string, unknown>, status: string) => void
  onToolResult?: (tool: string, result: string, status: string) => void
  onComplete?: (content: string, messageId: string) => void
  onError?: (errorCode: string, message: string) => void
}

/**
 * AI 对话 SSE 流式请求
 *
 * 使用 fetch + ReadableStream 消费 SSE 事件流，
 * 避免 axios 不原生支持 SSE 的问题。
 */
export async function chatStream(
  conversationId: string,
  content: string,
  callbacks: SSECallbacks,
): Promise<void> {
  const userStore = useUserStore()
  const baseURL = import.meta.env.MODE === 'development'
    ? ''
    : (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888')
  const url = `${baseURL}/v1/ai/chat/stream`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userStore.token}`,
    },
    body: JSON.stringify({ conversationId, content }),
  })
  if (!response.ok) {
    const errorText = await response.text()
    if (response.status === 401) {
      callbacks.onError?.('UNAUTHORIZED', '登录已过期，请重新登录')
      return
    }
    callbacks.onError?.('HTTP_ERROR', `请求失败: ${response.status} ${errorText}`)
    return
  }
  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError?.('STREAM_ERROR', '无法读取响应流')
    return
  }
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // 解析 SSE 事件（以双换行分隔）
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        if (!part.trim()) continue
        let eventType = ''
        let eventData = ''
        for (const line of part.split('\n')) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7)
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6)
          }
        }
        if (!eventType || !eventData) continue
        try {
          const data = JSON.parse(eventData)
          switch (eventType) {
            case 'ai_chunk':
              callbacks.onChunk?.(data.content, data.index)
              break
            case 'ai_tool_call':
              callbacks.onToolCall?.(data.tool, data.args, data.status)
              break
            case 'ai_tool_result':
              callbacks.onToolResult?.(data.tool, data.result, data.status)
              break
            case 'ai_complete':
              callbacks.onComplete?.(data.content, data.messageId)
              break
            case 'ai_error':
              callbacks.onError?.(data.error, data.message)
              break
          }
        } catch {
          // 忽略解析失败的单个事件
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}


// ==================== AI 会话管理 ====================

/** AI 会话信息 */
export interface AIConversation {
  id: string
  userId: string
  title: string | null
  status: number
  createdAt: number
  updatedAt: number
}

/** 创建 AI 会话 */
export function createAIConversation(title?: string): Promise<ApiResponse<{ data: AIConversation }>> {
  return request({
    url: '/v1/ai/conversation',
    method: 'post',
    data: title ? { title } : {},
  })
}

/** 获取 AI 会话列表 */
export function getAIConversationList(page = 1, pageSize = 20): Promise<ApiResponse<{
  list: AIConversation[]
  total: number
}>> {
  return request({
    url: '/v1/ai/conversation/list',
    method: 'get',
    params: { page, pageSize },
  })
}

/** 删除 AI 会话 */
export function deleteAIConversation(conversationId: string): Promise<ApiResponse<void>> {
  return request({
    url: '/v1/ai/conversation/delete',
    method: 'post',
    data: { conversationId },
  })
}

/** 获取 AI 会话历史消息 */
export function getAIMessages(conversationId: string, page = 1, pageSize = 20): Promise<ApiResponse<{
  list: Array<{
    id: string
    sendId: string
    msgContent: string
    sendTime: number
  }>
  total: number
}>> {
  return request({
    url: `/v1/ai/conversation/${conversationId}/messages`,
    method: 'get',
    params: { page, pageSize },
  })
}


// 创建群聊
export function createGroup(data: {
  groupId: string
  groupName: string
  memberIds: string[]
}): Promise<ApiResponse<void>> {
  return request({
    url: '/v1/group/create',
    method: 'post',
    data
  })
}

// 添加群成员（邀请）
export function inviteGroupMembers(groupId: string, memberIds: string[]): Promise<ApiResponse<void>> {
  return request({
    url: `/v1/group/${groupId}/invite`,
    method: 'post',
    data: { memberIds }
  })
}

// 移除群成员
export function removeGroupMember(groupId: string, memberId: string): Promise<ApiResponse<void>> {
  return request({
    url: `/v1/group/${groupId}/remove`,
    method: 'post',
    data: { memberId }
  })
}

// 退出群组
export function exitGroup(groupId: string): Promise<ApiResponse<void>> {
  return request({
    url: `/v1/group/${groupId}/exit`,
    method: 'post'
  })
}

// 修改群组信息
export function updateGroup(groupId: string, data: {
  name?: string
  avatar?: string
}): Promise<ApiResponse<void>> {
  return request({
    url: `/v1/group/${groupId}`,
    method: 'put',
    data
  })
}

// 解散群组
export function dismissGroup(groupId: string): Promise<ApiResponse<void>> {
  return request({
    url: `/v1/group/${groupId}`,
    method: 'delete'
  })
}

// 获取会话历史消息
export function getChatHistory(conversationId: string, page = 1, count = 50): Promise<ApiResponse<{
  count: number
  data: Array<{
    id: string
    conversationId: string
    sendId: string
    sendName: string | null
    recvId: string | null
    recvName: string | null
    chatType: number
    msgContent: string
    sendTime: number | null
    createAt: number | null
  }>
}>> {
  return request({
    url: `/v1/chat/conversation/${conversationId}`,
    method: 'get',
    params: { page, count }
  })
}

// 获取群组列表
export function getGroupList(params?: GroupListParams): Promise<ApiResponse<PageData<GroupListItem>>> {
  return request({
    url: '/v1/group/list',
    method: 'get',
    params: { page: 1, count: 100, ...params }
  })
}

// 获取群组详情
export function getGroupInfo(groupId: string): Promise<ApiResponse<GroupInfo>> {
  return request({
    url: `/v1/group/${groupId}`,
    method: 'get'
  })
}

// 获取未读消息列表
export function getUnreadList(params?: {
  conversationType?: 1 | 2
}): Promise<ApiResponse<UnreadListResponse>> {
  return request({
    url: '/v1/chat/unread/list',
    method: 'post',
    data: params || {}
  })
}

// 清除会话未读
export function clearUnread(data: ClearUnreadRequest): Promise<ApiResponse<void>> {
  return request({
    url: '/v1/chat/unread/clear',
    method: 'post',
    data
  })
}
