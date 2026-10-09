export function formatNumber(value) {
  if (value === null || value === undefined || value === '') return ''
  return String(Math.round(Number(value))).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export const onlyDigits = (value) => String(value ?? '').replace(/\D/g, '')

/** Yozish jarayonida telefonni +998 90 123 45 67 ko'rinishiga keltiradi */
export function formatPhoneInput(value) {
  let digits = onlyDigits(value)
  if (digits.length < 3) return '+998 '
  if (!digits.startsWith('998')) digits = `998${digits}`
  digits = digits.slice(0, 12)
  const rest = digits.slice(3)
  const parts = [rest.slice(0, 2), rest.slice(2, 5), rest.slice(5, 7), rest.slice(7, 9)].filter(Boolean)
  return `+998 ${parts.join(' ')}`
}

export function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
}

export function percent(part, total) {
  if (!total) return 0
  return Math.round((part / total) * 100)
}

/** Qidiruv uchun: kichik harf, apostrof variantlarini birxillashtirish */
export function normalizeText(value = '') {
  return String(value).toLowerCase().replace(/[‘’ʻʼ`']/g, "'").trim()
}

export function toLines(text = '') {
  return String(text)
    .split('\n')
    .map((l) => l.replace(/^[\s•\-–*]+/, '').trim())
    .filter(Boolean)
}

/** 1536000 -> "1.5 MB" */
export function formatBytes(bytes) {
  const n = Number(bytes)
  if (!n) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

/** Telefon raqamni solishtirish uchun: oxirgi 9 raqam */
export const phoneKey = (value) => onlyDigits(value).slice(-9)

/** Har qanday ko‘rinishdagi raqamni +998 90 123 45 67 formatiga keltiradi (import uchun) */
export function normalizePhone(value) {
  const digits = onlyDigits(value)
  if (!digits) return ''
  const local = digits.length >= 9 ? digits.slice(-9) : digits
  return formatPhoneInput(`998${local}`)
}

/** "Familiya Ism [Otasining ismi]" → { lastName, firstName } */
export function splitName(fullName = '') {
  const parts = String(fullName).trim().split(/\s+/).filter(Boolean)
  return { lastName: parts[0] || '', firstName: parts.slice(1).join(' ') }
}

/** Jadvalni CSV (Excel’da ochiladi) qilib yuklab olish */
export function downloadCsv(fileName, header, rows) {
  const esc = (v) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",;\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const text = [header, ...rows].map((r) => r.map(esc).join(';')).join('\r\n')
  const blob = new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/** Xodim ism qismlari: alohida maydonlar bo‘lmasa — F.I.Sh dan ajratiladi */
export function nameParts(e) {
  if (!e) return { lastName: '', firstName: '', middleName: '' }
  if (e.firstName || e.lastName) return { lastName: e.lastName || '', firstName: e.firstName || '', middleName: e.middleName || '' }
  const parts = String(e.fullName || '').trim().split(/\s+/).filter(Boolean)
  return { lastName: parts[0] || '', firstName: parts[1] || '', middleName: parts.slice(2).join(' ') }
}

/** "Familiya Ism Otasining ismi" */
export const joinName = (last, first, middle) => [last, first, middle].map((x) => String(x || '').trim()).filter(Boolean).join(' ')

/** 5000000 → "5 000 000 so‘m" */
export const formatMoney = (n) => (n === null || n === undefined || n === '' ? '—' : `${formatNumber(n)} so‘m`)

/** Telegram: "@username" ko‘rinishi va havola */
export const telegramHandle = (v) => {
  const s = String(v || '').trim().replace(/^https?:\/\/t\.me\//i, '').replace(/^@/, '')
  return s ? `@${s}` : ''
}
export const telegramLink = (v) => (telegramHandle(v) ? `https://t.me/${telegramHandle(v).slice(1)}` : null)
