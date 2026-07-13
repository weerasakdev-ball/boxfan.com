// ===================================================
// articles.js — ฐานข้อมูลบทความ Boxfan (ระบบใหม่)
// หมวดหมู่ที่มี: 'technique' (วิเคราะห์แทคติก), 'news' (ข่าวสาร), 'gear' (รีวิวอุปกรณ์)
// ===================================================

var ARTICLES = [

    // 🔽 นำบทความใหม่ล่าสุด มาวางไว้บนสุดตรงนี้เสมอ 🔽

   {
    cat     : 'technique',
    image   : 'https://res.cloudinary.com/dia2yts2f/image/upload/v1779866148/ChatGPT_Image_27_%E0%B8%9E.%E0%B8%84._2569_14_14_58.png',
    title   : 'เทคนิค MMA ขั้นสูง: วิเคราะห์ฟิสิกส์และชีวกลศาสตร์ระดับโลก',
    excerpt : 'ผ่าตัด 7 เทคนิคระดับแชมป์โลก ตั้งแต่ Calf Kick ทำลายเส้นประสาท Muay Thai Plum ควบคุมกระดูกสันหลัง Dagestani Handcuff ของ Khabib ไปจนถึง Inside Heel Hook ที่น่าสะพรึงกลัวที่สุดใน MMA',
    file    : 'articles/th/mma-advanced-techniques.html',
    date    : '2026-05-27'
},
    {
    cat     : 'technique',
    image   : 'https://res.cloudinary.com/dia2yts2f/image/upload/v1779850581/ChatGPT_Image_27_%E0%B8%9E.%E0%B8%84._2569_09_54_53.png',
    title   : 'ประวัติศาสตร์มวยสากล: จากกำปั้นโบราณ 6,000 ปีสู่ตำนานไทยระดับโลก',
    excerpt : 'เปิดเส้นทาง 6,000 ปีของมวยสากล ตั้งแต่เอธิโอเปีย กรีกโบราณ กฎควีนส์เบอร์รี โม่สัมบุณณานนท์คนแรกชนะมวยฝรั่ง จนถึงตำนาน 5 คนที่เขย่าวงการโลก',
    file    : 'articles/th/boxing-history-legends.html',
    date    : '2026-05-27'
},
    {
    cat     : 'technique',
    image   : 'https://res.cloudinary.com/dia2yts2f/image/upload/v1779853285/ChatGPT_Image_27_%E0%B8%9E.%E0%B8%84._2569_10_41_35.png',
    title   : 'ประวัติศาสตร์มวยไทย: จากสนามรบโบราณสู่โอลิมปิก ฉบับสมบูรณ์',
    excerpt : 'เจาะลึกกำเนิดมวยโบราณ ตำนานนายขนมต้ม 4 สกุลมวยบูรพา วิทยาศาสตร์ต้นกล้วย-มะพร้าว ยุคทองสมาร์ท-ดีเซลน้อย จนถึงวันที่ IOC รับรองมวยไทยอย่างเป็นทางการ',
    file    : 'articles/th/muay-thai-complete-history.html',
    date    : '2026-05-27'
},
    {
    cat     : 'technique',
    image   : 'https://res.cloudinary.com/dia2yts2f/image/upload/v1779864576/ChatGPT_Image_27_%E0%B8%9E.%E0%B8%84._2569_13_49_23.png',
    title   : 'รถถัง จิตรเมืองนนท์ — ประวัติรอบด้าน จากเด็กกรีดยางสู่แชมป์โลกค่าตัว 17 ล้าน',
    excerpt : 'เจาะลึกชีวิต "The Iron Man" ตั้งแต่รับจ้างล้างจานในงานศพ สู่แชมป์โลก ONE พร้อมถอดบทเรียนคดีฟ้อง 542 ล้านและวิกฤตวินัยที่วงการมวยไทยต้องเรียนรู้',
    file    : 'articles/th/rodtang-jitmuangnon-profile.html',
    date    : '2026-05-27'
},

{
    cat     : 'technique',
    image   : 'https://res.cloudinary.com/dia2yts2f/image/upload/v1779853780/ChatGPT_Image_27_%E0%B8%9E.%E0%B8%84._2569_10_49_59.png',
    title   : 'ตัดน้ำหนักมวย: วิทยาศาสตร์ อันตราย และประวัติศาสตร์ที่เขียนด้วยเลือด',
    excerpt : 'เปิดกลไก 4 ขั้นตอนที่นักสู้ใช้รีดน้ำออกจากร่างกาย พร้อมเจาะลึกอันตรายระดับเซลล์ และโศกนาฏกรรมที่บีบให้ ONE, WBC, NCAA ต้องปฏิรูประบบทั้งใบ',
    file    : 'articles/th/weight-cutting-combat-sports-science.html',
    date    : '2026-05-27'
},

{
    cat     : 'technique',
    image   : 'https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=800&fit=crop',
    title   : 'ระบบให้คะแนน UFC: ถอดรหัส Unified Rules พร้อมการปฏิรูปปี 2025',
    excerpt : 'เจาะลึก 10-Point Must System ลำดับขั้น Plan A/B/C กลไก Sliding Scale และกฎใหม่ปี 2025 ที่สถาปนา "Damage" เป็นหัวใจการตัดสิน — ทำไมครอบงำโดยไม่ทำร้ายคู่ต่อสู้ถึงไม่ได้ 10-8 อีกต่อไป',
    file    : 'articles/th/ufc-scoring-system.html',
    date    : '2026-05-27'
},
{
    cat     : 'technique',
    image   : 'https://images.unsplash.com/photo-1615117972428-28de67cda58e?w=800&fit=crop',
    title   : 'การให้คะแนนมวยไทย 2569: ราชดำเนิน WBC และ ONE Championship',
    excerpt : 'ปฏิรูปครั้งประวัติศาสตร์ — ห้ามเต้นยก 5 โทษ 4 ระดับ ระบบ VAR ครั้งแรก เปิดเผยคะแนนยกต่อยก เทียบระบบ WBC vs ONE Championship ที่ใช้นวม 4 ออนซ์',
    file    : 'articles/th/muay-thai-scoring-2026.html',
    date    : '2026-05-27'
},
{
    cat     : 'technique',
    image   : 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Madame_Tussauds_Bangkok_%2893%29.jpg',
    title   : 'นักมวยไทยใน IBHOF: ผู้ที่ได้รับการบรรจุ ผู้ที่รอคิว และอคติเชิงโครงสร้าง',
    excerpt : 'เขาทราย โผน กิ่งเพชรได้รับการบรรจุแล้ว แต่วีระพล พงษ์ศักดิ์เล็ก ชาติชายยังรอ — เจาะลึกว่าทำไมนักมวยไทยที่สถิติเหนือกว่าตะวันตกหลายคนถึงยังต้องนั่งรอบน Ballot',
    file    : 'articles/th/thai-boxers-ibhof.html',
    date    : '2026-05-27'
},
{
    cat     : 'technique',
    image   : 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&fit=crop',
    title   : 'การให้คะแนนมวยสากล: 4 เกณฑ์หลัก กรณีศึกษา Pacquiao-Bradley และมวยโอลิมปิก',
    excerpt : 'ถอดรหัส 4 เกณฑ์ที่กรรมการใช้จริง เจาะกรณีคำตัดสิน Pacquiao vs Bradley ที่ทำให้โลกตะลึง พร้อมเปรียบเทียบระบบมวยอาชีพกับโอลิมปิกที่ต่างกันกว่าที่คิด',
    file    : 'articles/th/boxing-scoring-system.html',
    date    : '2026-05-27'
},
    // 🔼 จบบทความ 🔼
];