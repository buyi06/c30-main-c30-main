import { showToast as vantShowToast } from 'vant'

export function showToast(msg, duration = 2000) {
  vantShowToast({ message: msg, duration })
}
