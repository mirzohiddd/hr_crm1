/**
 * Mock rejimda yuklangan hujjat fayllarini brauzerning IndexedDB omborida saqlaydi
 * (localStorage katta fayllar uchun yetmaydi). Backend ulanganda ishlatilmaydi.
 */
const DB_NAME = 'hr-crm-files'
const STORE = 'files'
let dbPromise = null

function open() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    if (!('indexedDB' in globalThis)) return reject(new Error('Brauzer fayllarni saqlashni qo‘llab-quvvatlamaydi'))
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error || new Error('Fayl omborini ochib bo‘lmadi'))
  })
  dbPromise.catch(() => (dbPromise = null))
  return dbPromise
}

async function tx(mode, fn) {
  const db = await open()
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE, mode)
    const result = fn(t.objectStore(STORE))
    t.oncomplete = () => resolve(result.result)
    t.onerror = () => reject(t.error || new Error('Fayl bilan ishlashda xatolik'))
  })
}

export const fileStore = {
  put: (id, blob) => tx('readwrite', (s) => s.put(blob, id)),
  get: (id) => tx('readonly', (s) => s.get(id)),
  remove: (id) => tx('readwrite', (s) => s.delete(id)),
  clear: () => tx('readwrite', (s) => s.clear()),
}
