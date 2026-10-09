/**
 * Yangi xodim uchun 7 kunlik o‘quv dasturi (boshlang‘ich matnlar).
 * Sozlamalar → Darslar bo‘limida tahrirlanadi.
 * Backend ulanganda: GET /lessons
 */
export const lessons = [
  {
    id: 1,
    day: 1,
    title: 'Kompaniya bilan tanishuv',
    duration: 60,
    description: 'Kompaniya tarixi, missiyasi, tuzilmasi va jamoa bilan tanishish.',
    content:
      'Kompaniyaning qisqacha tarixi va qadriyatlari\nBo‘limlar va ularning vazifalari\nRahbarlar va murojaat tartibi\nIsh joyi, jihozlar va aloqa kanallari',
    link: '',
  },
  {
    id: 2,
    day: 2,
    title: 'Ichki tartib qoidalari',
    duration: 45,
    description: 'Ish vaqti, kiyinish qoidalari, xavfsizlik va intizom talablari.',
    content: 'Ish vaqti 09:00 – 18:00, tushlik 13:00 – 14:00\nKechikish va ruxsat so‘rash tartibi\nKiyinish qoidalari\nMaxfiylik va axborot xavfsizligi',
    link: '',
  },
  {
    id: 3,
    day: 3,
    title: 'Mahsulot va xizmatlar',
    duration: 90,
    description: 'Kompaniya mahsulotlari, narxlar va eng ko‘p beriladigan savollar.',
    content: 'Asosiy mahsulotlar va ularning afzalliklari\nNarxlar va chegirmalar siyosati\nYetkazib berish shartlari\nKo‘p beriladigan savollar va javoblar',
    link: '',
  },
  {
    id: 4,
    day: 4,
    title: 'Mijozlar bilan muloqot',
    duration: 90,
    description: 'Muloqot standarti, e’tirozlar bilan ishlash va norozi mijoz bilan gaplashish.',
    content: 'Salomlashish va o‘zini tanishtirish standarti\nMijoz ehtiyojini aniqlash\nE’tirozlar bilan ishlash\nNorozi mijoz bilan muloqot qoidalari',
    link: '',
  },
  {
    id: 5,
    day: 5,
    title: 'CRM va ish vositalari',
    duration: 60,
    description: 'Ichki tizimlar, buyurtma kiritish va hisobot berish tartibi.',
    content: 'CRM tizimiga kirish va buyurtma kiritish\nIchki chat va vazifalar\nKunlik hisobot shakli\nParol va hisob xavfsizligi',
    link: '',
  },
  {
    id: 6,
    day: 6,
    title: 'Lavozim bo‘yicha amaliyot',
    duration: 120,
    description: 'Tajribali xodim (murabbiy) yonida real ish jarayonida amaliyot.',
    content: 'Murabbiy bilan birga ish jarayonini kuzatish\nMustaqil vazifalarni murabbiy nazoratida bajarish\nXatolar ustida ishlash',
    link: '',
  },
  {
    id: 7,
    day: 7,
    title: 'Takrorlash va yakuniy tayyorgarlik',
    duration: 60,
    description: 'O‘tilgan mavzularni takrorlash va yakuniy testga tayyorgarlik.',
    content: '1–6 kun mavzularini takrorlash\nSavol-javob\nYakuniy testga tayyorgarlik',
    link: '',
  },
]
