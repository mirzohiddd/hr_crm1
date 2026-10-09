// Deterministik tasodifiy sonlar generatori (mock ma'lumotlar har safar bir xil chiqishi uchun).
export function createRng(seed) {
  let a = seed >>> 0
  return function rng() {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export const pick = (rng, list) => list[Math.floor(rng() * list.length)]

export const randInt = (rng, min, max) => Math.floor(rng() * (max - min + 1)) + min

export function shuffle(rng, list) {
  const arr = [...list]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

export function weightedPick(rng, entries) {
  const total = entries.reduce((sum, [, w]) => sum + w, 0)
  let r = rng() * total
  for (const [value, weight] of entries) {
    r -= weight
    if (r <= 0) return value
  }
  return entries[entries.length - 1][0]
}

export function hashString(value) {
  let h = 2166136261
  for (let i = 0; i < value.length; i++) {
    h ^= value.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}
