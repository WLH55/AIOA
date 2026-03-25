import request from '@/utils/request'
import type { ApiResponse, ChatRequest, ChatResponse, GroupListParams, PageData, GroupListItem, GroupInfo, UnreadListResponse, ClearUnreadRequest } from '@/types'

// AI聊天
export function chat(data: ChatRequest): Promise<ApiResponse<ChatResponse>> {
  return request({
    url: '/v1/chat',
    method: 'post',
    data
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
