/**
 * Backend bilan aloqa (HR CRM backendi, login talab qilinmaydigan ochiq endpointlar):
 *   GET  /public/final-test            20 ta savol — to‘g‘ri javoblarsiz (havola/token talab qilinmaydi)
 *   POST /public/final-test/register   { firstName, lastName, age, birthDate, clientId } → { participant: { id, key, ... } }
 *   POST /public/final-test/submit     { participantId, participantKey, answers, durationSec, clientId }
 *                                      → { result: { submittedAt, fullName }, message } — ball backendda hisoblanadi va
 *                                        nomzodga qaytarilmaydi (natijani faqat HR CRM ko‘radi)
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

export const finalApi = {
  open: () => request('/public/final-test'),
  register: (body) => request('/public/final-test/register', { method: 'POST', body }),
  submit: (body) => request('/public/final-test/submit', { method: 'POST', body }),
}