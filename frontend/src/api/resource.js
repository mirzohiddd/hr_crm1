import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { table } from './mockDb'

/**
 * Mock "jadval" ustida CRUD. Backend endpointlarini taqlid qiladi.
 * @param {string} tableName mockDb jadvali nomi
 * @param {{ onCreate?: (data: object) => object }} options
 */
export function createMockCollection(tableName, { onCreate } = {}) {
  const t = table(tableName)
  const notFound = () => Promise.reject(new ApiError('Ma’lumot topilmadi', 404))

  return {
    list: () => mockResponse(t.all()),
    get: (id) => {
      const row = t.find(id)
      return row ? mockResponse(row) : notFound()
    },
    create: (data) => mockResponse(t.insert(onCreate ? onCreate(data) : data)),
    update: (id, data) => {
      const row = t.patch(id, data)
      return row ? mockResponse(row) : notFound()
    },
    remove: (id) => {
      t.remove(id)
      return mockResponse(null)
    },
  }
}

/**
 * REST resurs: VITE_API_URL bo'lsa haqiqiy API, aks holda mock.
 * FastAPI tomonda kutiladigan endpointlar:
 *   GET    {path}           ro'yxat
 *   GET    {path}/{id}      bitta yozuv
 *   POST   {path}           yaratish
 *   PUT    {path}/{id}      yangilash
 *   DELETE {path}/{id}      o'chirish
 */
export function createResource(path, tableName, options) {
  if (USE_MOCK) return createMockCollection(tableName, options)
  return {
    list: (params) => request(path, { params }),
    get: (id) => request(`${path}/${id}`),
    create: (data) => request(path, { method: 'POST', body: data }),
    update: (id, data) => request(`${path}/${id}`, { method: 'PUT', body: data }),
    remove: (id) => request(`${path}/${id}`, { method: 'DELETE' }),
  }
}
