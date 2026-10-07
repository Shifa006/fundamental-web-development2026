# คู่มือเตรียมตอบอาจารย์: Planit ทำงานอย่างไร

## 1. ภาพรวมใน 30 วินาที
Planit คือเว็บแพลนเนอร์นักศึกษา 4 หน้า (Today, Tasks, Courses, Projects) หน้าเว็บ (HTML/CSS/JS) เรียก JSON API ของ Django ด้วย `fetch` กฎสำคัญทั้งหมด (สถานะงาน, ความเร่งด่วน, โหมดสอบ, เกรดเป้าหมาย, ความคืบหน้าโปรเจกต์) คำนวณใน Python เท่านั้น JavaScript แสดงผล

ประโยคสรุปที่พูดได้: "Python ตัดสิน, JavaScript แสดง, ฐานข้อมูลเก็บ"

## 2. เส้นทางของคำขอหนึ่งครั้ง (เพิ่มงาน)
1. ผู้ใช้กรอกชื่อ กดบันทึก → handler ใน JS อ่านฟอร์ม
2. `api.js` เรียก `fetch("/api/tasks/", {method:"POST", headers:{X-CSRFToken}, body: JSON})`
3. Django: urls → middleware (ตรวจล็อกอิน) → view
4. `validators.py` ตรวจชื่อ วันที่ ตัวเลือก ถ้าผิด raise `PlanitValidationError`
5. view บันทึก `Task` พร้อม `owner = request.user`
6. สร้าง domain object (`to_domain_item`) คำนวณ status/คะแนน แล้วตอบ JSON 201
7. JS ได้ JSON → สร้างการ์ดด้วย `createElement` ใส่ข้อความด้วย `textContent` → ไม่โหลดหน้าใหม่
8. ถ้า error: server ตอบ 400 พร้อม message/field → `api.js` โยน Error → `catch` แสดงข้อความ → `finally` เปิดปุ่ม

## 3. กฎและตรรกะ
- **สถานะ** (เรียงตามลำดับตรวจ): completed → past_exam → no_date → overdue → today → upcoming
- **คะแนนความเร่งด่วน** = น้ำหนักความสำคัญ (urgent 3 / normal 2 / later 1) × ตัวคูณประเภท (general 1.00, assignment 1.00, study 1.25, exam 2.00, personal 0.50) ÷ (วันเหลือ + 1)
  - ตัวอย่าง: งานด่วนอีก 4 วัน = 3×1÷5 = 0.60; สอบปกติอีก 3 วัน = 2×2÷4 = 1.00 → สอบมาก่อน
  - งานเลยกำหนดอยู่กลุ่มแรก เรียงตามความสำคัญแล้วตามจำนวนวันที่เลย
- **โหมดสอบ**: สอบ 0–14 วันแสดง; งานปกติแสดงถ้าเลยกำหนด/ด่วนไม่เกิน 7 วัน/ปกติไม่เกิน 3 วัน; later ซ่อน; งานส่วนตัวแสดงเฉพาะ urgent แต่ละคลาสตัดสินเองด้วย `visible_in_exam_mode`
- **เกรดเป้าหมาย**: ต้องได้เฉลี่ย (เป้า − คะแนนที่ได้แล้ว) ÷ น้ำหนักที่เหลือ × 100. ตัวอย่าง ได้ 42 เหลือ 50 เป้า 80 → 76%; เป้า 95 → 106% เป็นไปไม่ได้
- **ความคืบหน้าโปรเจกต์** = งานเสร็จ ÷ งานทั้งหมดที่ผูกกับโปรเจกต์ (คำนวณ ไม่เก็บซ้ำ)

## 4. แผนที่หัวข้อวิชา → โค้ด
### Web Development
| หัวข้อ | อยู่ที่ไหน | พูดอย่างไร |
|---|---|---|
| HTML | templates/planner/*.html | semantic tag, label, ARIA |
| CSS | static/planner/css/style.css | ตัวแปรสี, ธีม, media query มือถือ |
| Bootstrap | ใช้หลักๆ กับ modal (ไฟล์ local); หน้าตา/เลย์เอาต์เป็น custom CSS | อย่าพูดว่า Bootstrap ออกแบบทุกอย่าง |
| Tailwind | ไม่ได้ใช้ | ต้องมี build step; Bootstrap เหมาะกับขนาดงานนี้ |
| JS fundamentals | โมดูลต่อหน้า | const/let, arrow function, template literal, destructuring |
| DOM | createElement, addEventListener | ไม่ใช้ innerHTML กัน XSS |
| High-order array | filter/map/sort/some/find | ค้นหา กรอง เรียง แสดงผล |
| Fetch/Promise/async-await | api.js, Promise.all ใน projects.js | Promise คือค่าที่มาในอนาคต; await รอผล |
| JSON/HTTP | views.py JsonResponse | GET/POST/PATCH/DELETE, 200/201/204/400/401/404 |
| AJAX | fetch | AJAX รุ่นใหม่: อัปเดตหน้าไม่รีโหลด |
| jQuery, React | ไม่ได้ใช้ | DOM+Fetch พอสำหรับ 4 หน้า และเรียนพื้นฐานชัด |
| Web Storage | localStorage | โหมดสอบ ธีม การปิดแบนเนอร์รายวัน |

### Functional Programming (Python)
- ฟังก์ชัน: `services.py` — top-down (`build_today_payload`), closure (`by_area`, `by_status`), `compose`, `select`(filter), `to_domain_items`(map), `status_counts`(reduce), default argument, lambda
- OOP: `domain.py` — abstraction (`PlannerItem` ABC), inheritance (+ `AssignmentItem` สืบจาก `GeneralItem`), polymorphism, encapsulation (`GradeComponent._score` + property), composition (`GradeBook`), `Module` + registry
- Exception: `validators.py` — `PlanitValidationError`, `try/except/else`; `transaction.atomic`

> ข้อควรยืนยัน: ฉันสมมติเนื้อหาวิชา Functional Programming ว่าเป็นฟังก์ชัน/OOP/exception ตามสเปกของคุณ ถ้าวิชาจริงมีหัวข้ออื่น (recursion, immutability, generator) ให้บอก ตอนนี้โค้ดไม่ได้ใช้ recursion และไม่ได้ใช้ `finally` ในฝั่ง Python

## 5. คำถามที่น่าจะโดน พร้อมคำตอบ
1. **ทำไมใช้ Django?** มี routing, ORM, auth, CSRF ให้ในตัว ลดโค้ดความปลอดภัยที่เขียนเอง; framework เรียกโค้ดเรา (inversion of control) ส่วน library เราเรียกมัน
2. **Polymorphism อยู่ตรงไหน?** ตอนเรียง/แสดงงานเรียก `item.attention_score(today)` กับทุกชนิด แต่ละคลาสคำนวณต่างกัน ไม่มี `if kind == ...`
3. **เพิ่มชนิดงานใหม่ต้องแก้อะไร?** เพิ่มคลาสลูกหนึ่งตัวและหนึ่งบรรทัดในตารางแมป
4. **ทำไมแยก domain.py กับ models.py?** models = โครงสร้างข้อมูลและการเก็บ; domain = พฤติกรรม/กฎ ทดสอบได้โดยไม่ต้องใช้ฐานข้อมูล
5. **CSRF คืออะไร?** เว็บอื่นหลอกให้เบราว์เซอร์ที่ล็อกอินอยู่ส่งคำขอแทนเรา; เราแนบ token ใน header `X-CSRFToken` และไม่ใช้ `csrf_exempt`
6. **ทำไมไม่ใช้ innerHTML?** ป้องกัน XSS; ใช้ `textContent` ข้อความถูกมองเป็นข้อความเสมอ
7. **fetch ต่างจาก XMLHttpRequest/jQuery อย่างไร?** fetch คืน Promise ใช้กับ async/await ได้ ไม่ต้องพึ่งไลบรารี
8. **async/await ทำงานอย่างไร?** `await` หยุดเฉพาะฟังก์ชันนั้นจนได้ผล โดยไม่บล็อกหน้าเว็บ
9. **ทำไมใช้ Python คำนวณแทน JS?** แหล่งความจริงเดียว ทดสอบได้ 104 เทสต์ และ "วันนี้" ใช้เวลาของเซิร์ฟเวอร์ เหมือนกันทุกเครื่อง
10. **เกรดเป้าหมายคิดอย่างไร?** ดูข้อ 3; น้ำหนักรวมต้อง 100; ใช้ Decimal
11. **ข้อมูลผู้ใช้คนอื่นเข้าถึงได้ไหม?** ไม่ได้: ทุกคำค้นกรองด้วย owner; id ของคนอื่นตอบ 404
12. **ทำไมไม่ใช้ React/Tailwind?** งานมี 4 หน้า DOM+Fetch เพียงพอ ไม่ต้องมี build step และโชว์พื้นฐานตามวิชา
13. **ถ้าฐานข้อมูลว่าง?** หน้าแสดงข้อความแนะนำ ไม่พัง
14. **ทดสอบอย่างไร?** unittest/Django test client 104 เทสต์ + ตรวจเบราว์เซอร์ 1360px/390px; การประเมินผู้ใช้ยังไม่ได้ทำ (บอกตรงๆ)
15. **ทำไมคะแนนตัวคูณสอบ 2.0?** เป็นค่าตั้งต้นที่ออกแบบเอง ไม่ได้มาจากสถิติ ปรับได้ที่ค่าคงที่เดียว

## 6. สิ่งที่ควรบอกตรงๆ ถ้าถูกถาม
- โค้ดต่างจากสเปก v1.2 สองจุด (ลำดับงานเลยกำหนด และโปรเจกต์นับสอบที่พลาด) — มีเทสต์ครอบ
- ทดสอบกับ Django 5.2.7 เท่านั้น (requirements ระบุ 6.1.2 ซึ่งยังไม่ได้รัน) — ก่อนส่งให้รัน `python manage.py test planner.tests` บนเครื่องตัวเองแล้วบันทึกผลใน docs/TEST_REPORT.md
- ยังไม่มีผลประเมินผู้ใช้; อ้างอิงในรายงานต้องตรวจก่อนส่ง
- ใช้ AI ช่วย — ใส่ในหัวข้อ Statement on the Use of AI ตามนโยบายวิชา

## 7. ข้อควรระวังเพิ่มเติม (ตรวจจากโค้ด)
- ระบบโมดูลเสริม (`Module` + registry) มีโครงแล้ว แต่ **registry ว่าง** ยังไม่มีโมดูลจริง อย่าพูดว่ามีโมดูลหลายตัว
- ฟอร์มสมัครสมาชิกมี HTML `pattern` + `minlength` + `title` ที่ช่องรหัสผ่าน (ให้ feedback ทันทีในเบราว์เซอร์) (อักขระพิเศษต้องไม่ใช่ช่องว่าง, ยาว 8–128) แต่ Django validators ฝั่งเซิร์ฟเวอร์ยังเป็นตัวตัดสิน เพราะข้ามฟอร์มได้ มีเทสต์ยืนยันทั้งสองชั้น
- JS มี `.reduce()` ใน `tasks.js` (`countByStatus`) แสดงจำนวนงานต่อสถานะในตัวกรอง Status เช่น `Overdue (1)` (อัปเดตทั้งมุมมอง List/Week/Month) ส่วน `status_counts` ฝั่ง Python (reduce) ใช้สรุปรายวิชาในหน้า Courses
- ไม่มีหน้า Account/เปลี่ยนรหัสผ่าน/รีเซ็ตรหัสผ่าน และไม่มี Google login
- ตัวกรอง/ค้นหาในหน้า Tasks ทำฝั่งเบราว์เซอร์ (filter/sort) ส่วน `/api/tasks/` คืนงานทั้งหมดของผู้ใช้
- ก่อนส่ง GitHub: ลบ `.venv/`, `db.sqlite3`, `__pycache__/`, `__MACOSX/`

## 8. ลำดับที่ `runserver` เปิดหน้าแรก
manage.py → config.settings (ROOT_URLCONF) → config/urls.py (include planner.urls) → planner/urls.py (path "" → today_page) → render today.html; ถ้ายังไม่ล็อกอิน middleware redirect ไป /login/?next=/ ก่อน
