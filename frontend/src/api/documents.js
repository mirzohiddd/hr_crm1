import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { createResource } from './resource'
import { table } from './mockDb'
import { fileStore } from '@/utils/fileStore'
import { randomToken } from '@/utils/hash'
import { todayISO } from '@/utils/date'

const base = createResource('/documents', 'documents')

export const documentsApi = {
  list: base.list,
  get: base.get,

  /** PATCH /documents/{id}/status */
  updateStatus(id, { status, comment = '', reviewedBy }) {
    if (USE_MOCK) return base.update(id, { status, comment, reviewedBy, reviewedAt: todayISO() })
    return request(`/documents/${id}/status`, { method: 'PATCH', body: { status, comment } })
  },

  /**
   * POST /documents (multipart/form-data): employeeId, type, status, comment, file
   */
  async upload({ employeeId, type, status = 'Tasdiqlangan', comment = '', file, uploadedBy }) {
    if (!USE_MOCK) {
      const form = new FormData()
      form.append('employeeId', String(employeeId))
      form.append('type', type)
      form.append('status', status)
      form.append('comment', comment)
      form.append('file', file)
      return request('/documents', { method: 'POST', body: form })
    }
    const fileId = `doc-${Date.now()}-${randomToken(4)}`
    try {
      await fileStore.put(fileId, file)
    } catch (e) {
      throw new ApiError(e.message || 'Faylni saqlab bo‘lmadi')
    }
    const today = todayISO()
    const approved = status === 'Tasdiqlangan'
    return mockResponse(
      table('documents').insert({
        employeeId,
        type,
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type || '',
        fileId,
        uploadedAt: today,
        uploadedBy,
        status,
        reviewedBy: approved ? uploadedBy : null,
        reviewedAt: approved ? today : null,
        comment,
      }),
    )
  },

  /** GET /documents/{id}/file — fayl (Blob). Namunaviy yozuvlarda fayl bo‘lmaydi → null */
  async getFile(doc) {
    if (!USE_MOCK) return request(`/documents/${doc.id}/file`, { responseType: 'blob' })
    if (!doc.fileId) return null
    const blob = await fileStore.get(doc.fileId)
    return blob || null
  },

  /** DELETE /documents/{id} */
  async remove(id) {
    if (!USE_MOCK) return request(`/documents/${id}`, { method: 'DELETE' })
    const doc = table('documents').find(id)
    if (doc?.fileId) await fileStore.remove(doc.fileId).catch(() => {})
    table('documents').remove(id)
    return mockResponse(null)
  },
}
