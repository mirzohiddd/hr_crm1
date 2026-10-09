/**
 * Google Sheets / CSV dan nomzodlarni import qilish uchun yordamchilar (kutubxonasiz).
 */
import { normalizeText, normalizePhone } from './format'
import { toISO } from './date'

/** CSV/TSV matnni qatorlarga ajratadi (qo‘shtirnoq ichidagi vergul va yangi qatorlarni hisobga oladi) */
export function parseCSV(text) {
  const src = String(text || '').replace(/^﻿/, '')
  const firstLine = src.split(/\r?\n/, 1)[0] || ''
  const counts = { ',': 0, ';': 0, '\t': 0 }
  let inQ = false
  for (const ch of firstLine) {
    if (ch === '"') inQ = !inQ
    else if (!inQ && ch in counts) counts[ch]++
  }
  const sep = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][1] ? Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0] : ','

  const rows = []
  let row = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < src.length; i++) {
    const ch = src[i]
    if (quoted) {
      if (ch === '"' && src[i + 1] === '"') {
        cell += '"'
        i++
      } else if (ch === '"') quoted = false
      else cell += ch
    } else if (ch === '"') quoted = true
    else if (ch === sep) {
      row.push(cell)
      cell = ''
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && src[i + 1] === '\n') i++
      row.push(cell)
      rows.push(row)
      row = []
      cell = ''
    } else cell += ch
  }
  if (cell || row.length) {
    row.push(cell)
    rows.push(row)
  }
  return rows.map((r) => r.map((c) => c.trim())).filter((r) => r.some(Boolean))
}

const HEADERS = {
  fullName: ['f.i.sh', 'fish', 'f.i.o', 'fio', 'ism', 'name', 'ismi', 'familiya', 'nomzod', 'фио', 'имя', 'full name'],
  phone: ['telefon', 'phone', 'tel', 'raqam', 'nomer', 'номер', 'телефон', 'mobile'],
  position: ['lavozim', 'position', 'vakansiya', 'yo\'nalish', 'yonalish', 'ish turi', 'должность', 'вакансия', 'job'],
  department: ['bo\'lim', 'bolim', 'brend', 'mahsulot', 'отдел', 'department'],
  source: ['manba', 'source', 'qayerdan', 'источник', 'kanal'],
  age: ['yosh', 'age', 'возраст', 'yoshi'],
  city: ['shahar', 'city', 'manzil', 'hudud', 'город', 'viloyat', 'tuman'],
  note: ['izoh', 'comment', 'note', 'xabar', 'комментарий', 'tajriba', 'qo\'shimcha'],
  date: ['sana', 'date', 'timestamp', 'vaqt', 'отметка времени', 'дата', 'vaqt belgisi'],
}

/** Sarlavha qatoridan ustunlar indeksini aniqlash */
export function detectColumns(header) {
  const map = {}
  const cells = header.map((h) => normalizeText(h))
  Object.entries(HEADERS).forEach(([key, words]) => {
    const index = cells.findIndex((c, i) => !Object.values(map).includes(i) && words.some((w) => c === w || c.includes(w)))
    if (index !== -1) map[key] = index
  })
  return map
}

function parseDate(value) {
  if (!value) return null
  // 08.10.2026 14:30:00 | 2026-10-08 14:30 | 10/8/2026 14:30:00
  let m = value.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})(?:[ ,T]+(\d{1,2}):(\d{2}))?/)
  if (m) {
    const [, a, b, y, h = '9', min = '00'] = m
    const [d, mo] = value.includes('/') ? [b, a] : [a, b]
    return `${y}-${mo.padStart(2, '0')}-${d.padStart(2, '0')}T${h.padStart(2, '0')}:${min}`
  }
  m = value.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/)
  if (m) return `${m[1]}-${m[2]}-${m[3]}T${m[4] || '09'}:${m[5] || '00'}`
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : `${toISO(d)}T09:00`
}

/** Matndagi lavozim nomini ro‘yxatdagi lavozimga moslash */
export function matchPosition(value, positions) {
  const v = normalizeText(value)
  if (!v) return null
  return (
    positions.find((p) => normalizeText(p.name) === v) ||
    positions.find((p) => v.includes(normalizeText(p.name)) || normalizeText(p.name).includes(v)) ||
    null
  )
}

const SOURCES = { instagram: 'Instagram', insta: 'Instagram', google: 'Google Sheets', sheet: 'Google Sheets', forma: 'Google Sheets', form: 'Google Sheets', tavsiya: 'Tavsiya', tanish: 'Tavsiya' }
function matchSource(value) {
  const v = normalizeText(value)
  const hit = Object.keys(SOURCES).find((k) => v.includes(k))
  return hit ? SOURCES[hit] : null
}

/**
 * CSV qatorlarini nomzodlarga aylantirish.
 * @returns {{ rows: Array, columns: object, hasHeader: boolean }}
 */
export function rowsToCandidates(table, positions, { defaultSource = 'Google Sheets', defaultPositionId = null, departments = [] } = {}) {
  if (!table.length) return { rows: [], columns: {}, hasHeader: false }
  let columns = detectColumns(table[0])
  const hasHeader = columns.fullName !== undefined || columns.phone !== undefined
  // Sarlavhasiz fayl: 1-ustun F.I.Sh, 2-ustun telefon, 3-ustun lavozim
  if (!hasHeader) columns = { fullName: 0, phone: 1, position: 2 }
  const body = hasHeader ? table.slice(1) : table
  const get = (r, key) => (columns[key] !== undefined ? r[columns[key]] || '' : '')

  const rows = body.map((r) => {
    const fullName = get(r, 'fullName').replace(/\s+/g, ' ').trim()
    const phone = normalizePhone(get(r, 'phone'))
    const positionText = get(r, 'position')
    const position = matchPosition(positionText, positions)
    const age = parseInt(get(r, 'age'), 10)
    const errors = []
    if (!fullName) errors.push('F.I.Sh yo‘q')
    if (phone.replace(/\D/g, '').length !== 12) errors.push('Telefon noto‘g‘ri')
    const positionId = position?.id ?? defaultPositionId
    if (!positionId) errors.push(positionText ? `“${positionText}” lavozimi topilmadi` : 'Lavozim yo‘q')
    return {
      fullName,
      phone,
      positionId,
      positionText,
      departmentId: matchPosition(get(r, 'department'), departments)?.id ?? null,
      source: matchSource(get(r, 'source')) || defaultSource,
      age: Number.isFinite(age) && age > 0 && age < 100 ? age : null,
      city: get(r, 'city'),
      note: get(r, 'note'),
      createdAt: parseDate(get(r, 'date')),
      errors,
    }
  })
  return { rows, columns, hasHeader }
}

/**
 * Google Sheets havolasini CSV eksport manziliga aylantirish.
 * Jadval "Havolaga ega har kim ko‘ra oladi" rejimida ulashilgan bo‘lishi kerak.
 */
export function googleSheetCsvUrl(url) {
  const m = String(url).match(/docs\.google\.com\/spreadsheets\/d\/(e\/)?([a-zA-Z0-9-_]+)/)
  if (!m) return null
  const gid = String(url).match(/[#&?]gid=(\d+)/)?.[1]
  // "Veb’da chop etish" havolasi (/d/e/...)
  if (m[1]) return `https://docs.google.com/spreadsheets/d/e/${m[2]}/pub?output=csv${gid ? `&gid=${gid}` : ''}`
  return `https://docs.google.com/spreadsheets/d/${m[2]}/gviz/tq?tqx=out:csv${gid ? `&gid=${gid}` : ''}`
}
