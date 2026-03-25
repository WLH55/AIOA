import type { WsMessage } from '@/types'

// WebSocket 关闭码常量（与服务端保持一致）
const WS_CLOSE_CODE = {
  NORMAL: 1000,
  GOING_AWAY: 1001,
  KICKED_BY_NEW_LOGIN: 4100,
  HEARTBEAT_TIMEOUT: 4101,
  KICKED_BY_ADMIN: 4102,
} as const

// 不应自动重连的关闭码
const NO_RECONNECT_CODES: number[] = [
  WS_CLOSE_CODE.KICKED_BY_NEW_LOGIN,
  WS_CLOSE_CODE.KICKED_BY_ADMIN,
]

// ==================== 全局单例管理 ====================
interface WsInstance {
  client: WebSocketClient
  token: string
  refCount: number  // 引用计数
}

const globalWsMap = new Map<string, WsInstance>()

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private token: string
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private messageHandlers: ((message: WsMessage) => void)[] = []
  private savedHandlers: ((message: WsMessage) => void)[] = [] // 保存处理器引用用于重连

  constructor(url: string, token: string) {
    this.url = url
    this.token = token
  }

  // 连接WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 在URL中添加token作为查询参数，因为浏览器WebSocket API无法设置自定义header
        const wsUrl = `${this.url}?token=${encodeURIComponent(this.token)}`
        console.log('正在连接WebSocket:', wsUrl.replace(/token=[^&]+/, 'token=***'))
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket连接成功')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WsMessage = JSON.parse(event.data)
            console.log(`[WebSocket底层] 收到消息，当前有${this.messageHandlers.length}个处理器`)
            this.messageHandlers.forEach((handler, index) => {
              console.log(`[WebSocket底层] 调用处理器 #${index + 1}`)
              handler(message)
            })
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          reject(error)
        }

        this.ws.onclose = (event: CloseEvent) => {
          console.log('WebSocket连接关闭', event.code, event.reason)
          this.stopHeartbeat()

          // 如果是被踢掉（4100 或 4102），不自动重连
          if (NO_RECONNECT_CODES.includes(event.code)) {
            console.log('被踢下线，不自动重连')
            return
          }

          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  // 发送消息
  send(message: WsMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket未连接')
    }
  }

  // 添加消息处理器
  onMessage(handler: (message: WsMessage) => void): void {
    console.log(`[WebSocket] 添加消息处理器，当前共${this.messageHandlers.length + 1}个`)
    this.messageHandlers.push(handler)
    this.savedHandlers.push(handler) // 同时保存到savedHandlers
  }

  // 移除消息处理器
  offMessage(handler: (message: WsMessage) => void): void {
    const index = this.messageHandlers.indexOf(handler)
    if (index > -1) {
      this.messageHandlers.splice(index, 1)
    }
    const savedIndex = this.savedHandlers.indexOf(handler)
    if (savedIndex > -1) {
      this.savedHandlers.splice(savedIndex, 1)
    }
  }

  // 关闭连接
  close(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    // 清除所有消息处理器,防止重复监听
    this.messageHandlers = []
  }

  // 尝试重连
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`尝试重连WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

      this.reconnectTimer = setTimeout(() => {
        this.connect().then(() => {
          // 重连成功后，重新注册所有保存的处理器
          this.messageHandlers = [...this.savedHandlers]
          console.log(`[WebSocket] 重连成功，重新注册了${this.messageHandlers.length}个处理器`)
        }).catch(error => {
          console.error('重连失败:', error)
        })
      }, 3000 * this.reconnectAttempts)
    } else {
      console.error('WebSocket重连失败，已达到最大重连次数')
    }
  }

  // 开始心跳
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        // 发送心跳包（可以根据后端需求调整）
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 每30秒发送一次心跳
  }

  // 停止心跳
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // 获取连接状态
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  // 判断是否已连接
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// ==================== 全局单例工厂函数 ====================

/**
 * 获取或创建 WebSocket 单例
 * @param token 认证 token
 * @returns WebSocketClient 实例
 */
export function getWebSocket(token: string): WebSocketClient {
  const wsUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8888'
  const fullUrl = `${wsUrl}/v1/ws/chat`

  // 检查是否已存在该 token 的连接
  let instance = globalWsMap.get(token)

  if (!instance) {
    // 创建新实例
    const client = new WebSocketClient(fullUrl, token)
    instance = { client, token, refCount: 0 }
    globalWsMap.set(token, instance)
    console.log('[WebSocket全局单例] 创建新连接')
  } else {
    console.log('[WebSocket全局单例] 复用已有连接')
  }

  // 增加引用计数
  instance.refCount++

  return instance.client
}

/**
 * 释放 WebSocket 引用
 * @param token 认证 token
 * @param client WebSocketClient 实例
 */
export function releaseWebSocket(token: string, client: WebSocketClient): void {
  const instance = globalWsMap.get(token)
  if (instance && instance.client === client) {
    instance.refCount--
    console.log(`[WebSocket全局单例] 释放引用，当前引用计数: ${instance.refCount}`)

    // 只有当引用计数为 0 时才关闭连接
    if (instance.refCount <= 0) {
      console.log('[WebSocket全局单例] 引用计数为0，关闭连接')
      client.close()
      globalWsMap.delete(token)
    }
  }
}

/**
 * 保持向后兼容：创建WebSocket实例的工厂函数（已废弃）
 * @deprecated 请使用 getWebSocket 替代
 */
export function createWebSocket(token: string): WebSocketClient {
  return getWebSocket(token)
}
