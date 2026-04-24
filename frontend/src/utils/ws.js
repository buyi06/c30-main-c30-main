/**
 * WebSocket日志客户端
 */

class LogWebSocket {
  constructor() {
    this.ws = null
    this.listeners = new Set()
    this.reconnectTimer = null
    this.shouldReconnect = true
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/logs`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('[WS] 已连接')
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const entry = JSON.parse(event.data)
        this.listeners.forEach(cb => {
          try { cb(entry) } catch (e) { /* ignore */ }
        })
      } catch (e) { /* ignore */ }
    }

    this.ws.onclose = () => {
      console.log('[WS] 已断开')
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000)
      }
    }

    this.ws.onerror = () => {
      this.ws.close()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  onMessage(cb) {
    this.listeners.add(cb)
    return () => this.listeners.delete(cb)
  }
}

// 全局单例
const ws = new LogWebSocket()
export default ws