/**
 * Mock rejim uchun boshlang‘ich ma'lumotlar bazasi.
 * Barcha jadvallar bir-biriga id orqali bog‘langan:
 *   employees.positionId / departmentId / candidateId (bo‘lim va lavozim mustaqil)
 *   candidates.positionId / departmentId / employeeId
 *   trainings.employeeId, testResults.employeeId / testId / trainingId
 *   documents.employeeId
 */
import { createRng, pick, randInt, weightedPick } from '@/utils/random'
import { addDays, todayISO } from '@/utils/date'
import { hashPassword, randomToken } from '@/utils/hash'
import { defaultDepartmentFor, departments, positions } from './catalog'
import { buildEmployees } from './employees'
import { lessons } from './lessons'
import { DEFAULT_PASS_PERCENT } from '@/constants'
import { defaultTestSettings, tests } from './tests'

const ADMIN_NAME = 'Rustamova Kamola'

const CANDIDATE_NAMES = [
  ['Qodirova Sevara', 'Ayol'], ['Toshmatov Jasur', 'Erkak'], ['Sobirova Malika', 'Ayol'], ['Ismoilov Bekzod', 'Erkak'],
  ['Usmonova Zarina', 'Ayol'], ['Haydarov Sanjar', 'Erkak'], ['Normatova Laylo', 'Ayol'], ['Umarov Islom', 'Erkak'],
  ['Hasanova Diyora', 'Ayol'], ['Tursunov Doniyor', 'Erkak'], ['Sultonova Mohira', 'Ayol'], ['Oripov Shohruh', 'Erkak'],
  ['Fayzullayeva Sabina', 'Ayol'], ['Saidov Akmal', 'Erkak'], ['Mirzayeva Munisa', 'Ayol'], ['Abdullayev Temur', 'Erkak'],
  ['Xolmatova Nigora', 'Ayol'], ['Rustamov Farrux', 'Erkak'], ['Jo‘rayeva Durdona', 'Ayol'], ['Karimov Nodir', 'Erkak'],
  ['Yusupova Feruza', 'Ayol'], ['Nazarov Javlon', 'Erkak'], ['Ergasheva Shahnoza', 'Ayol'], ['Aliyev Ulug‘bek', 'Erkak'],
  ['Rahimova Gulnora', 'Ayol'], ['Qodirov Dilshod', 'Erkak'], ['Tursunova Kamola', 'Ayol'], ['Hasanov Sherzod', 'Erkak'],
  ['Saidova Nilufar', 'Ayol'],
]
const CITIES = ['Toshkent', 'Toshkent', 'Toshkent', 'Chirchiq', 'Yangiyo‘l', 'Olmaliq']
const NOTES = [
  'Instagram’dagi e’lon orqali yozdi, tajribasi bor.',
  'Kechki smenada ishlay olishini aytdi.',
  'Avval savdo sohasida ishlagan.',
  'Rus tilini yaxshi biladi.',
  'Talaba, yarim kunlik ishga qiziqmoqda.',
  '',
  '',
]
const REJECT_REASONS = ['Suhbatga kelmadi', 'Ish grafigi to‘g‘ri kelmadi', 'Tajribasi yetarli emas', 'Maosh bo‘yicha kelishilmadi']
const PHONE_CODES = ['90', '91', '93', '94', '97', '99', '33', '88']

const PASS = DEFAULT_PASS_PERCENT

/** Javoblar: { [savolId]: variantIndeksi } — dastlabki `correct` tasi to‘g‘ri */
const answersFor = (test, correct) =>
  Object.fromEntries(test.questions.map((q, i) => [q.id, i < correct ? q.correctIndex : (q.correctIndex + 1) % q.options.length]))

export function buildSeed(today = todayISO()) {
  const rng = createRng(77)
  const at = (date, h = randInt(rng, 9, 17), m = pick(rng, ['00', '15', '30', '45'])) => `${date}T${String(h).padStart(2, '0')}:${m}`
  const phone = () => {
    const n = () => String(randInt(rng, 0, 9))
    return `+998 ${pick(rng, PHONE_CODES)} ${n()}${n()}${n()} ${n()}${n()} ${n()}${n()}`
  }

  const employees = buildEmployees(today)
  let employeeId = employees.length

  // ---------- Nomzodlar ----------
  // [holat, necha kun oldin kelgan, lavozim, manba]
  const PLAN = [
    ['Yangi', 0, 1, 'Instagram'], ['Yangi', 0, 2, 'Instagram'], ['Yangi', 1, 1, 'Google Sheets'], ['Yangi', 1, 5, 'Google Sheets'],
    ['Yangi', 2, 4, 'Instagram'], ['Yangi', 2, 1, 'Google Sheets'], ['Yangi', 3, 3, 'Instagram'],
    ['Bog‘lanildi', 3, 1, 'Instagram'], ['Bog‘lanildi', 4, 2, 'Google Sheets'], ['Bog‘lanildi', 5, 4, 'Tavsiya'], ['Bog‘lanildi', 5, 1, 'Google Sheets'],
    ['Suhbat', 4, 1, 'Instagram'], ['Suhbat', 6, 3, 'Google Sheets'], ['Suhbat', 6, 5, 'Instagram'], ['Suhbat', 7, 1, 'Tavsiya'],
    ['Ishga qabul qilindi', 9, 1, 'Instagram'], ['Ishga qabul qilindi', 12, 2, 'Google Sheets'], ['Ishga qabul qilindi', 13, 1, 'Instagram'],
    ['Ishga qabul qilindi', 15, 4, 'Google Sheets'], ['Ishga qabul qilindi', 17, 5, 'Instagram'], ['Ishga qabul qilindi', 20, 1, 'Tavsiya'],
    ['Rad etildi', 8, 1, 'Instagram'], ['Rad etildi', 10, 3, 'Google Sheets'], ['Rad etildi', 14, 2, 'Instagram'], ['Rad etildi', 18, 4, 'Boshqa'],
    ['Rad etildi', 21, 1, 'Google Sheets'],
    ['Bog‘lanilmadi', 2, 1, 'Instagram'], ['Bog‘lanilmadi', 3, 2, 'Google Sheets'], ['Bog‘lanilmadi', 5, 4, 'Instagram'],
  ]
  // Ishga olinganlarning o‘quv holati: tugatilgan kunlar soni va test natijasi
  const HIRED_PROGRESS = [
    { days: 0 }, { days: 2 }, { days: 4 }, { days: 7, test: 'pending' }, { days: 7, test: 'failed' }, { days: 7, test: 'passed' },
  ]

  const HIRE_AGO = [0, 2, 4, 8, 9, 11]

  const candidates = []
  const trainings = []
  const testResults = []
  const recentEmployees = []
  let hiredIndex = 0
  let interviewOffset = 0

  PLAN.forEach(([status, ago, positionId, source], i) => {
    const [fullName, gender] = CANDIDATE_NAMES[i]
    const createdAt = at(addDays(today, -ago))
    const history = [{ status: 'Yangi', at: createdAt, by: source === 'Google Sheets' ? 'Google Sheets importi' : ADMIN_NAME }]
    const c = {
      id: PLAN.length - i,
      fullName,
      gender,
      phone: phone(),
      age: randInt(rng, 18, 38),
      city: pick(rng, CITIES),
      positionId,
      departmentId: defaultDepartmentFor(positionId, i),
      source,
      status,
      contactAttempts: 0,
      note: pick(rng, NOTES),
      createdAt,
      interviewAt: null,
      rejectReason: '',
      employeeId: null,
      history,
    }
    const step = (s, dayOffset) => {
      const d = addDays(today, -Math.max(0, ago - dayOffset))
      history.push({ status: s, at: at(d), by: ADMIN_NAME })
    }
    if (status === 'Bog‘lanilmadi') {
      c.contactAttempts = 1 + (i % 2)
      for (let k = 0; k < c.contactAttempts; k++) step('Bog‘lanilmadi', 1 + k)
    } else if (status !== 'Yangi') step('Bog‘lanildi', 1)
    if (['Suhbat', 'Ishga qabul qilindi'].includes(status) || (status === 'Rad etildi' && i % 2 === 0)) {
      step('Suhbat', 2)
      // Suhbat bosqichidagilar uchun — bugun yoki yaqin kunlarda
      c.interviewAt = status === 'Suhbat' ? at(addDays(today, interviewOffset++), 10 + interviewOffset * 2, '00') : at(addDays(today, -Math.max(0, ago - 3)))
    }
    if (status === 'Rad etildi') {
      c.rejectReason = pick(rng, REJECT_REASONS)
      step('Rad etildi', 4)
    }
    if (status === 'Ishga qabul qilindi') {
      const progress = HIRED_PROGRESS[hiredIndex]
      const hireDate = addDays(today, -HIRE_AGO[hiredIndex])
      hiredIndex++
      history.push({ status: 'Ishga qabul qilindi', at: at(hireDate), by: ADMIN_NAME })
      const emp = {
        id: ++employeeId,
        fullName,
        gender,
        birthDate: `${2026 - c.age}-0${randInt(rng, 1, 9)}-1${randInt(rng, 0, 9)}`,
        phone: c.phone,
        email: '',
        address: `${c.city}`,
        departmentId: c.departmentId,
        age: c.age,
        positionId,
        hireDate,
        status: progress.test === 'passed' ? 'Faol' : 'Yangi',
        leftAt: null,
        candidateId: c.id,
        photo: null,
      }
      c.employeeId = emp.id
      recentEmployees.push(emp)

      // O‘quv dasturi
      const training = {
        id: trainings.length + 1,
        employeeId: emp.id,
        startDate: hireDate,
        completedDays: Array.from({ length: progress.days }, (_, d) => ({ day: d + 1, at: at(addDays(hireDate, d), 17, '30'), by: ADMIN_NAME })),
        status: progress.days === 7 ? 'Yakunlandi' : 'Jarayonda',
        finishedAt: progress.days === 7 ? at(addDays(hireDate, 6), 17, '30') : null,
        testResultId: null,
      }
      trainings.push(training)

      if (progress.test) {
        const test = positionId === 1 ? tests[1] : tests[0]
        const total = test.questions.length
        const result = {
          id: testResults.length + 1,
          employeeId: emp.id,
          testId: test.id,
          trainingId: training.id,
          passPercent: PASS,
          assignedAt: training.finishedAt,
          status: 'Kutilmoqda',
          score: null,
          correct: null,
          total,
          completedAt: null,
          attempts: [],
        }
        if (progress.test !== 'pending') {
          const passed = progress.test === 'passed'
          const correct = passed ? total - 1 : Math.max(0, Math.floor(total * (PASS / 100)) - 2)
          const score = Math.round((correct / total) * 100)
          const answers = answersFor(test, correct)
          const done = at(addDays(training.finishedAt.slice(0, 10), 1), 11, '00')
          result.attempts.push({ at: done, score, correct, total, passed, answers })
          Object.assign(result, { status: passed ? 'O‘tdi' : 'O‘tmadi', score, correct, completedAt: done })
        }
        testResults.push(result)
        training.testResultId = result.id
      }
    }
    candidates.push(c)
  })

  const allEmployees = [...recentEmployees.sort((a, b) => b.hireDate.localeCompare(a.hireDate)), ...employees]

  // Eski xodimlar ham o‘quv dasturidan o‘tgan (so‘nggi 3 oyda kelganlar)
  employees
    .filter((e) => e.status === 'Faol' && e.hireDate >= addDays(today, -90))
    .forEach((e) => {
      const training = {
        id: trainings.length + 1,
        employeeId: e.id,
        startDate: e.hireDate,
        completedDays: Array.from({ length: 7 }, (_, d) => ({ day: d + 1, at: at(addDays(e.hireDate, d), 17, '30'), by: ADMIN_NAME })),
        status: 'Yakunlandi',
        finishedAt: at(addDays(e.hireDate, 6), 17, '30'),
        testResultId: null,
      }
      trainings.push(training)
      const test = e.positionId === 1 ? tests[1] : tests[0]
      const total = test.questions.length
      const correct = randInt(rng, Math.ceil(total * 0.8), total)
      const score = Math.round((correct / total) * 100)
      const done = at(addDays(e.hireDate, 7), 11, '00')
      testResults.push({
        id: testResults.length + 1,
        employeeId: e.id,
        testId: test.id,
        trainingId: training.id,
        passPercent: PASS,
        assignedAt: training.finishedAt,
        status: 'O‘tdi',
        score,
        correct,
        total,
        completedAt: done,
        attempts: [{ at: done, score, correct, total, passed: true, answers: answersFor(test, correct) }],
      })
      training.testResultId = testResults.length
    })

  // ---------- Hujjatlar ----------
  const slug = (s) => s.toLowerCase().replace(/[‘’ʻʼ']/g, '').replace(/\s+/g, '_')
  const FILE_PREFIX = { Pasport: 'pasport', Diplom: 'diplom', CV: 'cv', 'Mehnat shartnomasi': 'mehnat_shartnomasi', 'Tibbiy ma’lumotnoma': 'tibbiy', Boshqa: 'hujjat' }
  const documents = []
  allEmployees.forEach((e) => {
    const recent = e.hireDate >= addDays(today, -14)
    const types = ['Pasport', 'Mehnat shartnomasi']
    if (rng() < 0.5) types.push(weightedPick(rng, [['Diplom', 3], ['CV', 4], ['Tibbiy ma’lumotnoma', 3]]))
    types.forEach((type, ti) => {
      const uploadedAt = addDays(e.hireDate, randInt(rng, 0, 3) - 1)
      const pending = recent && ti > 0 && rng() < 0.6
      documents.push({
        employeeId: e.id,
        type,
        fileName: `${FILE_PREFIX[type]}_${slug(e.fullName)}.pdf`,
        fileSize: randInt(rng, 180, 3800) * 1024,
        mimeType: 'application/pdf',
        fileId: null, // namunaviy yozuv: haqiqiy fayl yo‘q
        uploadedAt: uploadedAt > today ? today : uploadedAt,
        uploadedBy: ADMIN_NAME,
        status: pending ? 'Kutilmoqda' : 'Tasdiqlangan',
        reviewedBy: pending ? null : ADMIN_NAME,
        reviewedAt: pending ? null : uploadedAt > today ? today : uploadedAt,
        comment: '',
      })
    })
  })
  documents.sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt))
  const docs = documents.map((d, i) => ({ id: documents.length - i, ...d }))

  // ---------- Foydalanuvchilar ----------
  const user = (id, fullName, login, password, role, email, phoneNumber) => {
    const salt = randomToken(8)
    return {
      id,
      fullName,
      login,
      role,
      email,
      phone: phoneNumber,
      active: true,
      salt,
      passwordHash: hashPassword(password, salt),
      createdAt: addDays(today, -200),
      lastLoginAt: null,
    }
  }
  const users = [
    user(1, ADMIN_NAME, 'admin', 'admin123', 'admin', 'k.rustamova@kompaniya.uz', '+998 90 555 12 34'),
    user(2, 'Karimova Madina', 'hr', 'hr12345', 'hr', 'm.karimova@kompaniya.uz', '+998 91 234 56 78'),
  ]

  return {
    departments,
    positions,
    employees: allEmployees,
    candidates,
    lessons,
    trainings: trainings.sort((a, b) => b.id - a.id),
    tests,
    testResults: testResults.sort((a, b) => b.id - a.id),
    documents: docs,
    users,
    settings: [defaultTestSettings],
  }
}
