import request from '@/utils/request'
import type { ApiResponse } from '@/types'

/**
 * 知识库文件信息
 */
export interface KnowledgeDocument {
  id: string
  filename: string
  fileSize: number
  fileType: string
  chunkCount: number
  status: number  // 0=处理中, 1=已完成, 2=失败
  uploadTime: number
  updateTime: number
}

/**
 * 上传知识库文件
 *
 * 文件上传后状态为"处理中"(status=0)，
 * 需要在 AI 对话中发送指令让 Agent 调用 updateKnowledge 工具完成向量化。
 */
export function uploadKnowledgeFile(file: File): Promise<ApiResponse<KnowledgeDocument>> {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/v1/knowledge/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取知识库文档列表
 */
export function getKnowledgeList(
  page = 1,
  pageSize = 20
): Promise<ApiResponse<{ list: KnowledgeDocument[]; total: number }>> {
  return request({
    url: '/v1/knowledge/list',
    method: 'get',
    params: { page, pageSize }
  })
}

/**
 * 删除知识库文档
 */
export function deleteKnowledge(docId: string): Promise<ApiResponse<void>> {
  return request({
    url: '/v1/knowledge/delete',
    method: 'post',
    data: { id: docId }
  })
}

/**
 * 文档解析内容
 */
export interface DocumentContent {
  filename: string
  fileType: string
  content: string
}

/**
 * 获取文档解析内容（带行号/页码）
 */
export function getKnowledgeFileContent(docId: string): Promise<ApiResponse<DocumentContent>> {
  return request({
    url: `/v1/knowledge/file/${docId}/content`,
    method: 'get'
  })
}
