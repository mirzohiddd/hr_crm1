import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { table } from './mockDb'
import { hashPassword, randomToken } from '@/utils/hash'
import { nowLocal } from '@/utils/date'

/** Parol xeshi va tuzi tashqariga chiqmasligi uchun */
export const publicUser = ({ salt, passwordHash, ...rest }) => rest

const users = () => table('users')

export const authApi = {
  /**
   * POST /auth/login  { login, password } -> { access_token, user }
   */
  login(login, password) {
    if (!USE_MOCK) return request('/auth/login', { method: 'POST', body: { login, password } })
    const u = users().all().find((x) => x.login.toLowerCase() === String(login).trim().toLowerCase())
    if (!u || u.passwordHash !== hashPassword(password, u.salt)) {
      return mockResponse(null, 500).then(() => Promise.reject(new ApiError('Login yoki parol noto‘g‘ri', 401)))
    }
    if (!u.active) return Promise.reject(new ApiError('Hisobingiz bloklangan. Administratorga murojaat qiling.', 403))
    const updated = users().patch(u.id, { lastLoginAt: nowLocal() })
    // Mock token: "mock.<userId>.<tasodifiy>"
    return mockResponse({ access_token: `mock.${u.id}.${randomToken(12)}`, user: publicUser(updated) }, 500)
  },

  /** GET /auth/me — token hali amal qiladimi va foydalanuvchi faolmi */
  me(token) {
    if (!USE_MOCK) return request('/auth/me')
    const id = Number(String(token).split('.')[1])
    const u = users().find(id)
    if (!u || !u.active) return Promise.reject(new ApiError('Sessiya tugagan', 401))
    return mockResponse(publicUser(u), 0)
  },

  /** PUT /auth/me — o‘z profilini yangilash */
  updateMe(id, data) {
    if (!USE_MOCK) return request('/auth/me', { method: 'PUT', body: data })
    const { fullName, email, phone } = data
    return mockResponse(publicUser(users().patch(id, { fullName, email, phone })))
  },

  /** POST /auth/change-password { current_password, new_password } */
  changePassword(id, current, next) {
    if (!USE_MOCK) return request('/auth/change-password', { method: 'POST', body: { current_password: current, new_password: next } })
    const u = users().find(id)
    if (!u || u.passwordHash !== hashPassword(current, u.salt)) return Promise.reject(new ApiError('Joriy parol noto‘g‘ri', 400))
    const salt = randomToken(8)
    users().patch(id, { salt, passwordHash: hashPassword(next, salt) })
    return mockResponse(null)
  },
}

export const usersApi = {
  /** GET /users */
  list() {
    if (!USE_MOCK) return request('/users')
    return mockResponse(users().all().map(publicUser))
  },
  /** POST /users { fullName, login, password, role, email, phone, active } */
  create(data) {
    if (!USE_MOCK) return request('/users', { method: 'POST', body: data })
    const login = data.login.trim().toLowerCase()
    if (users().all().some((u) => u.login.toLowerCase() === login)) {
      return Promise.reject(new ApiError('Bu login band. Boshqa login tanlang.', 409))
    }
    const { password, ...rest } = data
    const salt = randomToken(8)
    const created = users().insert({ ...rest, login, salt, passwordHash: hashPassword(password, salt), createdAt: nowLocal().slice(0, 10), lastLoginAt: null })
    return mockResponse(publicUser(created))
  },
  /** PUT /users/{id} — password berilsa, parol yangilanadi */
  update(id, data) {
    if (!USE_MOCK) return request(`/users/${id}`, { method: 'PUT', body: data })
    const { password, ...rest } = data
    if (rest.login) {
      rest.login = rest.login.trim().toLowerCase()
      if (users().all().some((u) => u.id !== id && u.login.toLowerCase() === rest.login)) {
        return Promise.reject(new ApiError('Bu login band. Boshqa login tanlang.', 409))
      }
    }
    if (password) {
      rest.salt = randomToken(8)
      rest.passwordHash = hashPassword(password, rest.salt)
    }
    return mockResponse(publicUser(users().patch(id, rest)))
  },
  /** DELETE /users/{id} */
  remove(id) {
    if (!USE_MOCK) return request(`/users/${id}`, { method: 'DELETE' })
    users().remove(id)
    return mockResponse(null)
  },
}
