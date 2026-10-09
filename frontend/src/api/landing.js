import { ApiError, USE_MOCK, request } from './client'

/**
 * Nomzodlar testi natijalari (HR uchun). Test sahifasining o‘zi — alohida ilova: landing/ papkasi (/test/sotuv).
 * Savolnoma va baholash kaliti backendda (backend/app/landing_tests/<slug>.json), ball serverda hisoblanadi.
 * Mock rejimida (VITE_API_URL yo‘q) bu bo‘lim ishlamaydi — backend talab qilinadi.
 */
function requireBackend() {
  if (USE_MOCK) throw new ApiError('Nomzodlar testi backend bilan ishlaydi. frontend/.env da VITE_API_URL ni sozlang.', 503)
}

export const landingResultsApi = {
  async list() {
    requireBackend()
    return request('/landing-results')
  },
  async get(id) {
    requireBackend()
    return request(`/landing-results/${id}`)
  },
  async markViewed(id) {
    requireBackend()
    return request(`/landing-results/${id}/viewed`, { method: 'PATCH' })
  },
  async remove(id) {
    requireBackend()
    return request(`/landing-results/${id}`, { method: 'DELETE' })
  },
  async tests() {
    requireBackend()
    return request('/landing-tests')
  },
  async key(slug) {
    requireBackend()
    return request(`/landing-tests/${encodeURIComponent(slug)}/key`)
  },
}
