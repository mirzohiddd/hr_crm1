/**
 * Backend bilan aloqa (HR CRM backendi, login talab qilinmaydigan ochiq endpointlar):
 *   GET  /public/tests/{slug}          savollar (baholash kalitisiz); profil testida — bosqichlar (stages) va variantlar
 *   POST /public/tests/{slug}/submit   javoblar — hisoblash serverda
 *                                      (profil testi: answers = { savolId: 0 = «Qo‘shilmayman» | 1 = «Qo‘shilaman» })
 */
const BASE_URL = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.status = status
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
    if (typeof data?.detail === 'string') message = data.detail
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg) message = String(data.detail[0].msg).replace(/^Value error,\s*/, '')
    throw new ApiError(message, response.status)
  }
  return data
}

export const testApi = {
  get: (slug) => request(`/public/tests/${encodeURIComponent(slug)}`),
  submit: (slug, body) => request(`/public/tests/${encodeURIComponent(slug)}/submit`, { method: 'POST', body }),
}