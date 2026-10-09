/**
 * Testlar bazasi (boshlang‘ich ma'lumot).
 * positionIds bo‘sh bo‘lsa — test barcha lavozimlar uchun.
 * Backend ulanganda: GET /tests
 */
const q = (id, text, options, correctIndex) => ({ id, text, options, correctIndex })

export const tests = [
  {
    id: 1,
    title: 'Umumiy yakuniy test',
    description: '7 kunlik o‘quv dasturi bo‘yicha barcha yangi xodimlar uchun yakuniy test.',
    positionIds: [],
    passPercent: 80,
    active: true,
    questions: [
      q(1, 'Ish kuni soat nechada boshlanadi?', ['08:00', '09:00', '10:00', 'Erkin grafik'], 1),
      q(2, 'Ishga kechikadigan bo‘lsangiz nima qilishingiz kerak?', ['Hech narsa', 'Rahbarga oldindan xabar berish', 'Ertasi kuni aytish', 'Hamkasbga aytish'], 1),
      q(3, 'Mijoz ma’lumotlarini begonalarga berish mumkinmi?', ['Ha, so‘rasa', 'Faqat tanishlarga', 'Yo‘q, bu maxfiy ma’lumot', 'Faqat telefon raqamini'], 2),
      q(4, 'Mijoz bilan suhbat nimadan boshlanadi?', ['Narxni aytishdan', 'Salomlashish va o‘zini tanishtirishdan', 'Chegirma taklif qilishdan', 'Buyurtma raqamini so‘rashdan'], 1),
      q(5, 'Norozi mijoz bilan qanday gaplashish kerak?', ['Ovozni ko‘tarib', 'Xotirjam tinglab, yechim taklif qilib', 'Suhbatni tugatib', 'Rahbarga darhol uzatib'], 1),
      q(6, 'Buyurtmalar qayerga kiritiladi?', ['Daftarga', 'Shaxsiy telefonga', 'CRM tizimiga', 'Telegram guruhga'], 2),
      q(7, 'Hisob parolingizni hamkasbingizga aytish mumkinmi?', ['Ha', 'Yo‘q', 'Faqat rahbarga', 'Faqat bir marta'], 1),
      q(8, 'Kunlik hisobot qachon topshiriladi?', ['Hafta oxirida', 'Ish kuni yakunida', 'Oy oxirida', 'Talab qilinmaydi'], 1),
      q(9, 'Savolga javob bilmasangiz nima qilasiz?', ['Taxminiy javob beraman', 'Mijozni kuttirib, aniqlab javob beraman', 'Javob bermayman', 'Suhbatni uzaman'], 1),
      q(10, 'Murabbiy kim?', ['Yangi xodim', 'Tajribali xodim, amaliyotda yordam beradi', 'Mijoz', 'Tashqi tekshiruvchi'], 1),
    ],
  },
  {
    id: 2,
    title: 'Call Center testi',
    description: 'Call Center xodimlari uchun qo‘ng‘iroqlar standarti bo‘yicha test.',
    positionIds: [1],
    passPercent: 80,
    active: true,
    questions: [
      q(1, 'Qo‘ng‘iroqqa necha signal ichida javob berish kerak?', ['3 signal ichida', '10 signal', 'Farqi yo‘q', '1 daqiqa ichida'], 0),
      q(2, 'Suhbat boshida nima aytiladi?', ['Faqat “Allo”', 'Kompaniya nomi, ismingiz va salomlashish', 'Narxlar ro‘yxati', 'Hech narsa'], 1),
      q(3, 'Mijoz buyurtma bermasa nima qilinadi?', ['Qayta qo‘ng‘iroq qilmaslik', 'Sababini yozib, CRMda belgilash', 'Raqamni o‘chirish', 'Bahslashish'], 1),
      q(4, 'Buyurtma tasdiqlanganda mijozga nima aytiladi?', ['Hech narsa', 'Yetkazib berish sanasi va summasi', 'Faqat rahmat', 'Boshqa mahsulot narxi'], 1),
      q(5, 'Bir kunda nechta qo‘ng‘iroqlar hisobotga yoziladi?', ['Faqat muvaffaqiyatlilari', 'Barchasi', 'Faqat kiruvchilar', 'Hech biri'], 1),
    ],
  },
]

export const defaultTestSettings = {
  id: 1,
  passPercent: 80, // 80% va undan yuqori — testdan o‘tdi (barcha testlar uchun)
  maxAttempts: 3,
  shuffleQuestions: true,
  shuffleOptions: false,
  autoAssign: true, // 7-kun tugagach testni avtomatik yuborish
  activateOnPass: true, // testdan o‘tgan xodim statusini "Faol" ga o‘tkazish
}
