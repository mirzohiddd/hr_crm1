import { ref } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useToast } from './useToast'

/** Hujjatlar sahifasi va xodim profilida umumiy: ko‘rish, yuklab olish, o‘chirish, tasdiqlash */
export function useDocumentActions() {
  const store = useDocumentsStore()
  const toast = useToast()

  const detailId = ref(null)
  const busy = ref('')
  const deleteTarget = ref(null)
  const deleting = ref(false)
  const uploadOpen = ref(false)

  async function download(doc) {
    try {
      const blob = await store.getFile(doc)
      if (!blob) return toast.info('Fayl mavjud emas', 'Bu namunaviy yozuv — fayl biriktirilmagan')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.fileName
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      toast.error('Yuklab olib bo‘lmadi', e.message)
    }
  }

  function askDelete(doc) {
    deleteTarget.value = doc
  }

  async function confirmDelete() {
    const doc = deleteTarget.value
    deleting.value = true
    try {
      await store.remove(doc.id)
      if (detailId.value === doc.id) detailId.value = null
      toast.success('Hujjat o‘chirildi', doc.fileName)
      deleteTarget.value = null
    } catch (e) {
      toast.error('O‘chirib bo‘lmadi', e.message)
    } finally {
      deleting.value = false
    }
  }

  async function review(doc, nextStatus, comment) {
    busy.value = nextStatus === 'Tasdiqlangan' ? 'approve' : 'reject'
    try {
      await store.setStatus(doc.id, nextStatus, { comment })
      if (nextStatus === 'Tasdiqlangan') toast.success('Hujjat tasdiqlandi', doc.type)
      else toast.info('Hujjat rad etildi', 'Xodim hujjatni qayta topshirishi kerak')
      detailId.value = null
    } catch (e) {
      toast.error('Amalni bajarib bo‘lmadi', e.message)
    } finally {
      busy.value = ''
    }
  }

  return { detailId, busy, deleteTarget, deleting, uploadOpen, download, askDelete, confirmDelete, review }
}
