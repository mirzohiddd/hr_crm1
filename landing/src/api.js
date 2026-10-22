/**
 * Backend bilan aloqa (HR CRM backendi, login talab qilinmaydigan ochiq endpointlar):
 *   GET  /public/tests/{slug}          savollar (baholash kalitisiz); profil testida — bosqichlar (stages) va variantlar
 *   POST /public/tests/{slug}/phone-check  { phone } — savollardan oldin: raqam to‘g‘ri va band emasligi (409 — band)
 *   POST /public/tests/{slug}/submit   javoblar — hisoblash serverda (telefon majburiy, bitta raqam — bitta natija)
 *                                      (profil testi: answers = { savolId: 0 = «Qo‘shilmayman» | 1 = «Qo‘shilaman» },
 *                                       rasmli savollar: pictures = { rasmId: variant indeksi 0–3 })
 *   GET  /public/tests/{slug}/images/{name}  rasmli savol rasmi
 */
const BASE_URL = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status = 0, field = '') {
    super(message)
    this.status = status
    this.field = field // xato qaysi maydonga tegishli (masalan, 'phone') — backend 422 javobidan
  }
}

async function request(path, { method = 'GET', body } = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Serverga ulanib bo‘lmadi. Internet aloqasini tekshiring.')
  }
  let data = null
  try {
    data = await response.json()
  } catch {
    /* javob JSON emas */
  }
  if (!response.ok) {
    let message = `So‘rov bajarilmadi (${response.status})`
    let field = ''
    if (typeof data?.detail === 'string') message = data.detail
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      message = String(data.detail[0].msg).replace(/^Value error,\s*/, '')
      field = String(data.detail[0].loc?.at(-1) ?? '')
    }
    throw new ApiError(message, response.status, field)
  }
  return data
}

/** Backend bergan yo‘l (masalan, rasmli savol rasmi: /public/tests/sotuv/images/rasm-1.jpg) → to‘liq manzil */
export const assetUrl = (path) => (/^https?:\/\//.test(path || '') ? path : `${BASE_URL}${path || ''}`)

export const testApi = {
  get: (slug) => request(`/public/tests/${encodeURIComponent(slug)}`),
  checkPhone: (slug, phone) => request(`/public/tests/${encodeURIComponent(slug)}/phone-check`, { method: 'POST', body: { phone } }),
  submit: (slug, body) => request(`/public/tests/${encodeURIComponent(slug)}/submit`, { method: 'POST', body }),
}