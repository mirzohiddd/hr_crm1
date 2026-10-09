/**
 * Xodimlar uchun mock ma'lumotlar.
 * Backend ulanganda bu fayl o'rniga GET /employees javobi ishlatiladi.
 * Ma'lumotlar deterministik generator orqali yaratiladi; sanalar "bugun"ga nisbatan hisoblanadi.
 */
import { createRng, pick, randInt, shuffle } from '@/utils/random'
import { addDays, diffDays } from '@/utils/date'
import { defaultDepartmentFor, positions } from './catalog'

const SURNAMES = [
  'Aliyev', 'Karimov', 'Rahimov', 'Yusupov', 'Nazarov', 'Ergashev', 'Toshmatov', 'Sobirov', 'Qodirov',
  'Xolmatov', 'Abdullayev', 'Mirzayev', 'Ismoilov', 'Usmonov', 'Saidov', 'Rustamov', 'Jo‘rayev',
  'Haydarov', 'Normatov', 'Fayzullayev', 'Umarov', 'Hasanov', 'Tursunov', 'Sultonov', 'Oripov',
]
const MALE = [
  'Anvar', 'Jasur', 'Bobur', 'Sardor', 'Otabek', 'Rustam', 'Sherzod', 'Dilshod', 'Aziz', 'Javlon',
  'Temur', 'Ulug‘bek', 'Farrux', 'Nodir', 'Akmal', 'Bekzod', 'Sanjar', 'Shohruh', 'Islom', 'Doniyor',
]
const FEMALE = [
  'Madina', 'Dilnoza', 'Nilufar', 'Gulnora', 'Malika', 'Shahnoza', 'Sevara', 'Zarina', 'Kamola',
  'Feruza', 'Nigora', 'Munisa', 'Laylo', 'Diyora', 'Sabina', 'Mohira', 'Durdona',
]
const DISTRICTS = ['Yunusobod', 'Chilonzor', 'Mirzo Ulug‘bek', 'Yakkasaroy', 'Shayxontohur', 'Mirobod', 'Olmazor', 'Sergeli', 'Uchtepa', 'Yashnobod']
const STREETS = ['Amir Temur', 'Bobur', 'Navoiy', 'Mustaqillik', 'Shota Rustaveli', 'Bunyodkor', 'Oybek', 'Mukimiy', 'Nukus', 'Beruniy']
const PHONE_CODES = ['90', '91', '93', '94', '95', '97', '99', '33', '88']

// Lavozim bo‘yicha xodimlar soni
const HEADCOUNT = { 1: 16, 2: 6, 3: 6, 4: 7, 5: 5, 6: 3 }
// Lavozim bo‘yicha jins ehtimoli (ayol)
const FEMALE_RATE = { 1: 0.7, 2: 0.75, 3: 0.5, 4: 0.15, 5: 0.6, 6: 0.7 }

const slug = (s) => s.toLowerCase().replace(/[‘’ʻʼ']/g, '')

/**
 * @param {string} today YYYY-MM-DD
 * @returns {Array} xodimlar (id, departmentId, positionId bilan)
 */
export function buildEmployees(today) {
  const rng = createRng(20261008)
  const usedNames = new Set()

  const phone = () => {
    const n = () => String(randInt(rng, 0, 9))
    return `+998 ${pick(rng, PHONE_CODES)} ${n()}${n()}${n()} ${n()}${n()} ${n()}${n()}`
  }
  const address = () => `Toshkent sh., ${pick(rng, DISTRICTS)} tumani, ${pick(rng, STREETS)} ko‘chasi, ${randInt(rng, 1, 120)}-uy`
  const birthDate = (from, to) => `${randInt(rng, from, to)}-${String(randInt(rng, 1, 12)).padStart(2, '0')}-${String(randInt(rng, 1, 28)).padStart(2, '0')}`

  function person(positionId) {
    for (;;) {
      const female = rng() < FEMALE_RATE[positionId]
      const surname = pick(rng, SURNAMES)
      const fullName = female ? `${surname}a ${pick(rng, FEMALE)}` : `${surname} ${pick(rng, MALE)}`
      if (usedNames.has(fullName)) continue
      usedNames.add(fullName)
      return { fullName, gender: female ? 'Ayol' : 'Erkak' }
    }
  }

  const earliest = addDays(today, -365 * 4)
  const latestOld = addDays(today, -30)
  const span = diffDays(earliest, latestOld)

  const list = []
  Object.entries(HEADCOUNT).forEach(([pid, count]) => {
    const position = positions.find((p) => p.id === Number(pid))
    for (let i = 0; i < count; i++) {
      const p = person(position.id)
      const [surname, name] = p.fullName.split(' ')
      const hasEmail = position.id !== 5 && rng() < 0.8
      list.push({
        ...p,
        birthDate: birthDate(1980, 2005),
        phone: phone(),
        email: hasEmail ? `${slug(name)}.${slug(surname)}@kompaniya.uz` : '',
        address: address(),
        departmentId: defaultDepartmentFor(position.id, i),
        positionId: position.id,
        hireDate: addDays(earliest, Math.floor(Math.sqrt(rng()) * span)),
        status: 'Faol',
        leftAt: null,
        age: null,
        candidateId: null,
        photo: null,
      })
    }
  })

  // Bir nechta xodim ishdan ketgan
  shuffle(rng, list.map((_, i) => i))
    .slice(0, 5)
    .forEach((i) => {
      const e = list[i]
      e.status = 'Faol emas'
      e.leftAt = addDays(e.hireDate, randInt(rng, 60, Math.max(61, diffDays(e.hireDate, today) - 5)))
      if (e.leftAt > today) e.leftAt = addDays(today, -randInt(rng, 5, 40))
    })

  return list
    .sort((a, b) => b.hireDate.localeCompare(a.hireDate))
    .map((e, i, arr) => ({ id: arr.length - i, ...e }))
}
