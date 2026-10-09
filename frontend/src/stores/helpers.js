import { ref } from 'vue'

/**
 * Ro‘yxat bilan ishlaydigan store'lar uchun umumiy holat va CRUD amallari.
 * @param {{ list: Function, create?: Function, update?: Function, remove?: Function }} api
 * @param {string} errorMessage yuklashdagi xato matni
 */
export function useCollection(api, errorMessage) {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const loaded = ref(false)
  let pending = null

  async function fetchAll({ force = false } = {}) {
    if (loaded.value && !force) return
    if (pending && !force) return pending
    loading.value = true
    error.value = null
    pending = (async () => {
      try {
        items.value = await api.list()
        loaded.value = true
      } catch (e) {
        error.value = e.message || errorMessage
      } finally {
        loading.value = false
        pending = null
      }
    })()
    return pending
  }

  /** Server javobidagi yozuvni ro‘yxatga qo‘shish yoki yangilash */
  function upsert(row, { prepend = true } = {}) {
    if (!row) return row
    const index = items.value.findIndex((x) => x.id === row.id)
    if (index !== -1) items.value[index] = row
    else if (prepend) items.value.unshift(row)
    else items.value.push(row)
    return row
  }

  function drop(id) {
    items.value = items.value.filter((x) => x.id !== id)
  }

  async function create(payload) {
    return upsert(await api.create(payload))
  }

  async function update(id, payload) {
    return upsert(await api.update(id, payload))
  }

  async function remove(id) {
    await api.remove(id)
    drop(id)
  }

  const findById = (id) => items.value.find((x) => x.id === Number(id)) || null

  return { items, loading, error, loaded, fetchAll, upsert, drop, create, update, remove, findById }
}
