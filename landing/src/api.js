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
  constructor(message, status = 0, field = '', technical = '', raw = null) {
    super(message)
    this.status = status
    this.field = field // xato qaysi maydonga tegishli (masalan, 'phone') — backend 422 javobidan
    this.technical = technical // asl xato matni ("durationSec: Input should be ...") — yashirilmaydi, kichik shriftda ko‘rsatiladi
    this.raw = raw // backend javobi (detail) to‘liq
  }
}

// 422 (FastAPI/Pydantic) xatolari: maydon nomi va xato turi → tushunarli o‘zbekcha matn
const FIELD_LABELS = {
  fullName: 'F.I.Sh.', age: 'Yosh', date: 'Sana', position: 'Lavozim', phone: 'Telefon raqami',
  answers: 'Javoblar', pictures: 'Rasmli savollar', durationSec: 'Test vaqti', clientId: 'So‘rov identifikatori',
}
function friendlyValidation(item) {
  const loc = (item.loc || []).filter((x) => x !== 'body')
  const field = String(loc[0] ?? '')
  const label = FIELD_LABELS[field] || field || 'Ma’lumot'
  const ctx = item.ctx || {}
  const msg = String(item.msg || '')
  // Backend o‘zbekcha yozgan xatolar (ValueError) — o‘zi tushunarli
  if (item.type === 'value_error') return msg.replace(/^Value error,\s*/, '')
  const byType = {
    missing: `${label} kiritilmagan`,
    less_than_equal: `${label} qiymati juda katta (eng ko‘pi ${ctx.le})`,
    less_than: `${label} qiymati juda katta`,
    greater_than_equal: `${label} qiymati juda kichik (kamida ${ctx.ge})`,
    greater_than: `${label} qiymati juda kichik`,
    int_parsing: `${label} butun son bo‘lishi kerak`,
    int_type: `${label} butun son bo‘lishi kerak`,
    int_from_float: `${label} butun son bo‘lishi kerak`,
    string_too_short: `${label} juda qisqa`,
    string_too_long: `${label} juda uzun`,
    string_pattern_mismatch: `${label} formati noto‘g‘ri`,
    string_type: `${label} matn bo‘lishi kerak`,
    dict_type: `${label} noto‘g‘ri formatda yuborildi`,
  }
  const text = byType[item.type] || `${label}: ma’lumot noto‘g‘ri`
  return field === 'durationSec' ? `${text}. Sahifani yangilab, «Testni yakunlash» ni qayta bosing.` : text
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
    let technical = ''
    if (typeof data?.detail === 'string') message = data.detail
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      const item = data.detail[0]
      message = friendlyValidation(item)
      field = String(item.loc?.at(-1) ?? '')
      technical = data.detail.map((d) => `${(d.loc || []).filter((x) => x !== 'body').join('.')}: ${d.msg}`).join('; ')
    }
    throw new ApiError(message, response.status, field, technical, data?.detail ?? null)
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