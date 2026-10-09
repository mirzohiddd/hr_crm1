/**
 * Mock rejim uchun brauzerdagi "ma'lumotlar bazasi".
 * Har bir jadval localStorage'da saqlanadi, shuning uchun sahifa yangilanganda
 * nomzodlar, darslar progressi, test natijalari va boshqalar yo‘qolmaydi.
 * Backend (VITE_API_URL) ulanganda bu modul ishlatilmaydi.
 */
import { buildSeed } from '@/data/seed'
import { departments as NEW_DEPARTMENTS } from '@/data/catalog'
import { DEFAULT_PASS_PERCENT } from '@/constants'
import { fileStore } from '@/utils/fileStore'

const PREFIX = 'hr-crm:db:'
const VERSION_KEY = `${PREFIX}version`
// Tuzilma o‘zgarsa versiyani oshiring va MIGRATIONS ga ko‘chirish funksiyasini yozing —
// foydalanuvchi kiritgan ma'lumotlar saqlanib qoladi.
const VERSION = '3'

/**
 * v2 → v3:
 *  - bo‘limlar: Dermolife, Gepomer, Halila, Marketing, Boshqa (lavozimdan mustaqil)
 *  - test javoblari { savolId: javob } ko‘rinishiga o‘tkaziladi
 *  - o‘tish chegarasi 80% — mavjud natijalar qayta baholanadi
 */
function migrateV2toV3(db) {
  // Bo‘limlar: yangi ro‘yxat; eski "Marketing" saqlanadi, qolgan eski standart bo‘limlar "Boshqa" ga
  const OLD_DEFAULT = ['Sotuv', 'Logistika', 'Xo‘jalik', 'HR']
  const oldDepts = db.departments || []
  const custom = oldDepts.filter((d) => !OLD_DEFAULT.includes(d.name) && !NEW_DEPARTMENTS.some((n) => n.name === d.name))
  let nextId = Math.max(5, ...oldDepts.map((d) => d.id)) + 1
  const departments = [...NEW_DEPARTMENTS.map((d) => ({ ...d })), ...custom.map((d) => ({ ...d, id: nextId++ }))]
  const byName = Object.fromEntries(departments.map((d) => [d.name, d.id]))
  // Nomi mos kelsa (Marketing yoki qo‘lda qo‘shilgan bo‘lim) — o‘sha, aks holda "Boshqa"
  const remap = Object.fromEntries(oldDepts.map((d) => [d.id, byName[d.name] ?? byName.Boshqa]))
  db.departments = departments
  db.employees = (db.employees || []).map((e) => ({ ...e, departmentId: remap[e.departmentId] ?? byName.Boshqa }))
  db.candidates = (db.candidates || []).map((c) => ({ ...c, departmentId: c.departmentId ? remap[c.departmentId] ?? null : null, contactAttempts: c.contactAttempts || 0 }))
  db.positions = (db.positions || []).map(({ departmentId, ...p }) => p)

  // Testlar: 80% qoidasi
  const tests = Object.fromEntries((db.tests || []).map((t) => [t.id, t]))
  db.tests = (db.tests || []).map((t) => ({ ...t, passPercent: DEFAULT_PASS_PERCENT }))
  db.settings = (db.settings || []).map(({ defaultPassPercent, ...st }) => ({ ...st, passPercent: DEFAULT_PASS_PERCENT }))
  db.testResults = (db.testResults || []).map((r) => {
    const test = tests[r.testId]
    const attempts = (r.attempts || []).map((a) => {
      let answers = a.answers || {}
      if (Array.isArray(answers) && test) answers = Object.fromEntries(test.questions.map((q, i) => [q.id, answers[i]]))
      return { ...a, answers, passed: a.score >= DEFAULT_PASS_PERCENT }
    })
    const last = attempts.at(-1)
    return {
      ...r,
      passPercent: DEFAULT_PASS_PERCENT,
      attempts,
      status: last ? (last.passed ? 'O‘tdi' : 'O‘tmadi') : r.status,
    }
  })
  return db
}

const MIGRATIONS = { 2: migrateV2toV3 }

export const TABLES = [
  'departments',
  'positions',
  'employees',
  'candidates',
  'lessons',
  'trainings',
  'tests',
  'testResults',
  'documents',
  'users',
  'settings',
]

const memory = {}
let ready = false

function save(name) {
  try {
    localStorage.setItem(PREFIX + name, JSON.stringify(memory[name]))
  } catch {
    /* storage to‘lgan yoki mavjud emas — ma'lumot faqat xotirada qoladi */
  }
}

function readStorage(name) {
  try {
    const raw = localStorage.getItem(PREFIX + name)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function seedAll() {
  const seed = buildSeed()
  TABLES.forEach((name) => {
    memory[name] = seed[name] || []
    save(name)
  })
  try {
    localStorage.setItem(VERSION_KEY, VERSION)
  } catch {
    /* e'tiborsiz */
  }
}

function init() {
  if (ready) return
  ready = true
  let version = null
  try {
    version = localStorage.getItem(VERSION_KEY)
  } catch {
    /* e'tiborsiz */
  }
  const known = version && (version === VERSION || MIGRATIONS[version])
  const loaded = known ? TABLES.map((n) => [n, readStorage(n)]) : []
  if (!loaded.length || !loaded.every(([, rows]) => Array.isArray(rows))) return seedAll()

  let db = Object.fromEntries(loaded)
  let v = Number(version)
  // Eski versiyadagi ma'lumotlarni bosqichma-bosqich yangilash (o‘chirmasdan)
  while (String(v) !== VERSION && MIGRATIONS[v]) {
    db = MIGRATIONS[v](db)
    v++
  }
  TABLES.forEach((n) => (memory[n] = db[n] || []))
  if (String(version) !== VERSION) {
    TABLES.forEach(save)
    try {
      localStorage.setItem(VERSION_KEY, VERSION)
    } catch {
      /* e'tiborsiz */
    }
  }
}

/** Sinxron jadval: mock API modullari ichida ishlatiladi */
export function table(name) {
  const rows = () => {
    init()
    return memory[name]
  }
  const nextId = () => rows().reduce((max, r) => Math.max(max, Number(r.id) || 0), 0) + 1

  return {
    all: () => rows(),
    find: (id) => rows().find((r) => r.id === Number(id)) || null,
    where: (fn) => rows().filter(fn),
    insert(data) {
      const row = { ...data, id: nextId() }
      memory[name] = [row, ...rows()]
      save(name)
      return row
    },
    patch(id, data) {
      const list = rows()
      const index = list.findIndex((r) => r.id === Number(id))
      if (index === -1) return null
      list[index] = { ...list[index], ...data, id: list[index].id }
      save(name)
      return list[index]
    },
    remove(id) {
      memory[name] = rows().filter((r) => r.id !== Number(id))
      save(name)
    },
  }
}

/** Demo ma'lumotlarni boshlang‘ich holatga qaytarish (Sozlamalar → Tizim) */
export async function resetMockDb() {
  ready = true
  seedAll()
  try {
    await fileStore.clear()
  } catch {
    /* IndexedDB mavjud emas */
  }
}
