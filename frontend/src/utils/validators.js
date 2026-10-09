import { ageFrom } from './date'
import { onlyDigits } from './format'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export const isEmail = (value) => EMAIL_RE.test(String(value).trim())
export const isUzPhone = (value) => /^998\d{9}$/.test(onlyDigits(value))

function phoneError(value) {
  if (onlyDigits(value).length <= 3) return 'Telefon raqam kiritilishi shart'
  if (!isUzPhone(value)) return 'Raqamni to‘liq kiriting: +998 90 123 45 67'
  return null
}

function fullNameError(value) {
  const name = String(value || '').trim()
  if (!name) return 'F.I.Sh kiritilishi shart'
  if (name.split(/\s+/).length < 2) return 'Familiya va ismni to‘liq kiriting'
  return null
}

/** Email ixtiyoriy — faqat kiritilgan bo‘lsa tekshiriladi */
function optionalEmailError(value) {
  if (!String(value || '').trim()) return null
  return isEmail(value) ? null : 'Email formati noto‘g‘ri, masalan: ism@kompaniya.uz'
}

const NAME_RE = /^[\p{L}\s'‘’ʻʼ`-]{2,40}$/u
export const TELEGRAM_RE = /^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$/

export function validateEmployee(form) {
  const e = {}
  const first = String(form.firstName || '').trim()
  const last = String(form.lastName || '').trim()
  const middle = String(form.middleName || '').trim()
  if (!first) e.firstName = 'Ismni kiriting'
  else if (!NAME_RE.test(first)) e.firstName = 'Faqat harflar (2–40 belgi)'
  if (!last) e.lastName = 'Familiyani kiriting'
  else if (!NAME_RE.test(last)) e.lastName = 'Faqat harflar (2–40 belgi)'
  if (middle && !NAME_RE.test(middle)) e.middleName = 'Faqat harflar (2–40 belgi)'

  const phone = phoneError(form.phone)
  if (phone) e.phone = phone

  const tg = String(form.telegram || '').trim()
  if (tg && !TELEGRAM_RE.test(tg)) e.telegram = 'Masalan: @username (5–32 belgi, lotin harflari)'

  const email = optionalEmailError(form.email)
  if (email) e.email = email

  if (form.expectedSalary !== '' && form.expectedSalary !== null && form.expectedSalary !== undefined) {
    const n = Number(form.expectedSalary)
    if (!Number.isFinite(n) || n < 0) e.expectedSalary = 'To‘g‘ri summa kiriting'
    else if (n > 1_000_000_000) e.expectedSalary = 'Summa juda katta'
  }

  if (form.birthDate) {
    const age = ageFrom(form.birthDate)
    if (age < 16) e.birthDate = 'Xodim kamida 16 yoshda bo‘lishi kerak'
    else if (age > 80) e.birthDate = 'Tug‘ilgan sanani tekshiring'
  }

  if (!form.departmentId) e.departmentId = 'Bo‘limni tanlang'
  if (!form.positionId) e.positionId = 'Lavozimni tanlang'
  if (!form.hireDate) e.hireDate = 'Ishga qabul qilingan sanani tanlang'
  if (!form.status) e.status = 'Statusni tanlang'
  return e
}

export function validateCandidate(form) {
  const e = {}
  const name = fullNameError(form.fullName)
  if (name) e.fullName = name
  const phone = phoneError(form.phone)
  if (phone) e.phone = phone
  if (!form.positionId) e.positionId = 'Lavozimni tanlang'
  if (!form.source) e.source = 'Manbani tanlang'
  if (form.age !== '' && form.age !== null && form.age !== undefined) {
    const age = Number(form.age)
    if (!Number.isInteger(age) || age < 16 || age > 70) e.age = 'Yosh 16 dan 70 gacha bo‘lsin'
  }
  return e
}

export function validateProfile(form) {
  const e = {}
  if (!form.fullName.trim()) e.fullName = 'Ism kiritilishi shart'
  const email = optionalEmailError(form.email)
  if (email) e.email = email
  if (onlyDigits(form.phone).length > 3) {
    const phone = phoneError(form.phone)
    if (phone) e.phone = phone
  }
  return e
}

export function validatePassword(password, confirm) {
  const e = {}
  if (!password) e.password = 'Parolni kiriting'
  else if (password.length < 6) e.password = 'Parol kamida 6 belgidan iborat bo‘lsin'
  if (confirm !== undefined && password !== confirm) e.confirm = 'Parollar mos kelmadi'
  return e
}

export function validateUser(form, { isNew }) {
  const e = {}
  if (!form.fullName.trim()) e.fullName = 'Ism kiritilishi shart'
  const login = form.login.trim()
  if (!login) e.login = 'Login kiritilishi shart'
  else if (!/^[a-zA-Z0-9._-]{3,32}$/.test(login)) e.login = 'Faqat lotin harflari, raqam va . _ - (3–32 belgi)'
  if (isNew || form.password) Object.assign(e, validatePassword(form.password))
  const email = optionalEmailError(form.email)
  if (email) e.email = email
  if (!form.role) e.role = 'Rolni tanlang'
  return e
}
