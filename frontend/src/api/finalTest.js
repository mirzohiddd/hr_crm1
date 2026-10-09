import { ApiError, USE_MOCK, request } from './client'

/**
 * Yakuniy bilim testi natijalari (HR uchun).
 * Test sahifasi — landing-2/ ilovasi: /test/yakuniy (ochiq, havola/token talab qilinmaydi).
 * Savollar va kalit: backend/app/landing_tests/yakuniy.json; ball faqat backendda hisoblanadi.
 */
function requireBackend() {
  if (USE_MOCK) throw new ApiError('Yakuniy bilim testi backend bilan ishlaydi. frontend/.env da VITE_API_URL ni sozlang.', 503)
}

export const finalTestApi = {
  async info() {
    requireBackend()
    return request('/final-test/info')
  },
  async results() {
    requireBackend()
    return request('/final-results')
  },
  async result(id) {
    requireBackend()
    return request(`/final-results/${id}`)
  },
  async remove(id) {
    requireBackend()
    return request(`/final-results/${id}`, { method: 'DELETE' })
  },
}
