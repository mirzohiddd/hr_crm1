/**
 * API qatlami.
 *
 * Vue komponentlar -> Pinia store -> API modul (shu papka) -> FastAPI -> PostgreSQL
 *
 * VITE_API_URL berilmagan bo'lsa, barcha modullar mock ma'lumotlar bilan ishlaydi.
 * Backend tayyor bo'lganda .env faylga VITE_API_URL yozish kifoya — komponentlar o'zgarmaydi.
 */
const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')

export const USE_MOCK = !BASE_URL || import.meta.env.VITE_USE_MOCK === 'true'
export const MOCK_DELAY = Number(import.meta.env.VITE_MOCK_DELAY ?? 450)

export class ApiError extends Error {
  constructor(message, status = 0, data = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

// Token auth store'dan beriladi (main.js da ulanadi).
let tokenProvider = () => null
export function setTokenProvider(fn) {
  tokenProvider = fn
}

// Server 401 qaytarsa (sessiya tugagan) — auth store foydalanuvchini login sahifasiga qaytaradi.
let unauthorizedHandler = () => {}
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

function buildUrl(path, params) {
  const query = params
    ? new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
      ).toString()
    : ''
  return `${BASE_URL}${path}${query ? `?${query}` : ''}`
}

function extractMessage(data, status) {
  if (!data) return `So‘rov bajarilmadi (${status})`
  // FastAPI: { detail: "..." } yoki { detail: [{ msg: "..." }] }
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail) && data.detail[0]?.msg) return String(data.detail[0].msg).replace(/^Value error,\s*/, '')
  return data.message || `So‘rov bajarilmadi (${status})`
}

/**
 * @param {string} path
 * @param {{ method?: string, body?: any, params?: object, headers?: object, responseType?: 'json' | 'blob' }} options
 * body FormData bo‘lsa (fayl yuklash) — multipart sifatida yuboriladi.
 */
export async function request(path, { method = 'GET', body, params, headers = {}, responseType = 'json' } = {}) {
  const token = tokenProvider()
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  let response
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers: {
        Accept: responseType === 'blob' ? '*/*' : 'application/json',
        ...(body !== undefined && !isForm ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    })
  } catch {
    throw new ApiError('Serverga ulanib bo‘lmadi. Internet aloqasini tekshiring.')
  }

  if (!response.ok) {
    let data = null
    try {
      data = await response.json()
    } catch {
      /* javob JSON emas */
    }
    if (response.status === 401 && token) unauthorizedHandler()
    throw new ApiError(extractMessage(data, response.status), response.status, data)
  }
  if (response.status === 204) return null
  return responseType === 'blob' ? response.blob() : response.json()
}

export const clone = (value) => (value === undefined ? value : JSON.parse(JSON.stringify(value)))
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

/** Mock javob: tarmoq kechikishini taqlid qiladi va ma'lumot nusxasini qaytaradi */
export async function mockResponse(data, ms = MOCK_DELAY) {
  await wait(ms)
  return clone(data)
}
