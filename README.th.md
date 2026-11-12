# REA-Video-Pro-Max

## ถอดวิธีตัดต่อ แล้วสร้างเนื้อหาใหม่ในสไตล์เดียวกัน

**เปลี่ยนวิดีโออ้างอิงเป็นไทม์ไลน์ที่มีหลักฐานและเทมเพลตสไตล์ที่ใช้ซ้ำได้ จากนั้นใส่สคริปต์และสื่อชุดใหม่เพื่อเรนเดอร์วิดีโอของคุณ**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[ตัวอย่างที่บันทึกไว้](docs/index.html) · [วิดีโอ A](docs/media/reference.mp4) · [วิดีโอ B](docs/media/adapted.mp4) · [ผลตรวจสอบ (English)](docs/VALIDATION.md)

งานตัดต่อที่ดีประกอบด้วยการตัดสินใจหลายอย่าง ทั้งจุดตัด กลุ่มคำ คำที่เน้น การเคลื่อนไหว และจังหวะเสียง REA-Video-Pro-Max ช่วยให้ตรวจสอบและใช้ส่วนที่รองรับของระบบนี้ซ้ำได้

```text
วิดีโอ A → วิเคราะห์และอนุมานไทม์ไลน์ → เทมเพลตสไตล์＋เนื้อหาใหม่ → โปรเจกต์แก้ไขได้ → วิดีโอ B
```

ตัวอย่างใช้สื่อสังเคราะห์ที่โปรเจกต์เป็นเจ้าของ A และ B มีข้อความและสื่อต่างกัน เว็บไซต์แบบ static แสดงผลที่บันทึกไว้ ไม่ประมวลผล inference สดหรืออัปโหลดวิดีโอของผู้เข้าชม

## ใช้ทำงานอะไรได้บ้าง

- แยกวิดีโอทั้งเรื่องเป็นช็อต สไตล์คำบรรยาย การเคลื่อนไหว คิวเสียง และไทม์ไลน์พร้อมหลักฐานตามเวลา
- วิเคราะห์ฟอนต์ องค์ประกอบและสีจากเฟรมเดียว ภาพนิ่งไม่สามารถยืนยันเวลาแอนิเมชันหรือเสียงได้
- นำสไตล์ที่สกัดได้ไปใช้กับสคริปต์ ภาพ หรือฟุตเทจใหม่เพื่อสร้างวิดีโออีกชิ้น
- หากขอเพียงการวิเคราะห์ สามารถส่งมอบไทม์ไลน์และไฟล์วิเคราะห์เป็นผลลัพธ์สมบูรณ์ได้

```text
ใช้ REA-Video-Pro-Max วิเคราะห์ไทม์ไลน์และสไตล์ของ reference.mp4 แล้วใช้สคริปต์ใหม่และไฟล์ของฉันสร้างวิดีโออีกชิ้นที่มีคำบรรยาย การเคลื่อนไหว และจังหวะคล้ายกัน ส่งเทมเพลต โปรเจกต์ วิดีโอ และข้อจำกัดที่ยังไม่ตรวจสอบ
```

## เริ่มให้ได้ผลลัพธ์แรก

ต้องมี Python 3.11+, FFmpeg และ FFprobe ส่วน Python ใช้ Pillow, NumPy และ PyAV ส่วน Tesseract สำหรับ OCR เป็นทางเลือก ภาษาที่ใช้ได้ขึ้นกับข้อมูลภาษาที่ติดตั้ง ดู[ขอบเขตการรองรับ (English)](docs/SUPPORT-MATRIX.md)

macOS เป็นแพลตฟอร์มพัฒนาที่ทดสอบจริง ส่วน Linux เป็นเป้าหมาย CI ที่วางไว้ และยังไม่รับรอง renderer แบบ native บน Windows การตรวจวิดีโอใหม่ต้องใช้บันทึก render ที่ hash ตรงกันและ OCR อิสระ ดังนั้นตัวอย่างครบขั้นตอนต้องมี Tesseract และข้อมูลภาษา `eng`

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

คำสั่งอ้างอิงโครงสร้าง Git checkout หากใช้แพ็กเกจ skill ที่แตกไฟล์แล้ว ให้เรียก `scripts/rea-video-pro-max.py` และเก็บ `lib`, `assets`, `references` ไว้ด้วยกัน ใช้ Python ที่ติดตั้ง dependencies แล้ว อย่าคัดลอกเฉพาะสคริปต์เริ่มต้น

## ใส่เนื้อหาใหม่ของคุณ

`examples/content.json` คือตัวอย่าง content binding แบบสังเคราะห์ แต่ละฉากใหม่มี `id`, `text`, `duration`, `background`, `accent` และ `asset` ถ้าต้องการ ส่วน `width`, `height`, `fps` กำหนดผลลัพธ์และอาจระบุ `audio`/`font` ได้ พาธสื่ออ้างอิงตำแหน่งไฟล์ binding โปรเจกต์คัดลอกไฟล์และบันทึก hash โดยไม่แอบนำภาพหรือเพลงของ A มาแทนเนื้อหา B คำพูดใหม่ต้องใช้เวลาใหม่ และระบุวิธีประมาณเมื่อไม่มี alignment ที่แม่นยำ

เสียงจากคลิปในแต่ละ scene จะถูกปิด หากต้องการเสียงให้กำหนด `audio` ใหม่แยกต่างหาก คลิปสั้นจะค้างเฟรมสุดท้าย และ renderer native ต้องใช้สื่อที่หันถูกทิศและมีพิกเซลสี่เหลี่ยมจัตุรัส CSV ส่งออกเฉพาะแถว shot โปรดตรวจข้อจำกัด shaping และการจัดกลุ่มก่อนใช้สคริปต์ซับซ้อนหรือข้อความสองทิศทาง

## ใช้กับ Claude Code / Codex

คัดลอกทั้งโฟลเดอร์ `skills/rea-video-pro-max` ไปยังไดเรกทอรี skill ของ host หรือให้ agent ติดตั้งจาก checkout นี้ ตำแหน่งในโปรเจกต์ที่พบบ่อยคือ `.claude/skills/rea-video-pro-max` และ `.agents/skills/rea-video-pro-max` การติดตั้ง skill ไม่ติดตั้ง FFmpeg ชุดภาษา OCR หรือน้ำหนักโมเดล บัญชี สิทธิ์รันและนโยบายข้อมูลของ host แยกจากโปรเจกต์นี้ [Skill](skills/rea-video-pro-max/SKILL.md) และเอกสารเทคนิคเป็น English

## ไฟล์และพฤติกรรมการส่งออก

- Native JSON เก็บผลวิเคราะห์ ไทม์ไลน์ ข้อมูลคำบรรยาย/สไตล์/การเคลื่อนไหว/เสียง เทมเพลตและโปรเจกต์ CSV ใช้ตรวจข้อมูลตัดต่อ
- SRT/WebVTT/ASS ส่งออกข้อความและเวลาตามความสามารถแต่ละรูปแบบ SRT ไม่รักษาสไตล์ตัวอักษรหรือการเคลื่อนไหวทั้งหมด
- ใช้เฉพาะ timeline adapter ที่เวอร์ชันติดตั้งรายงานว่า available ใบรับส่งออกระบุขอบเขต สิ่งที่ประมาณและข้อมูลที่สูญเสีย ไม่รับประกันทุกเอฟเฟกต์ในทุก editor
- ซอฟต์แวร์เรนเดอร์ประกอบเนื้อหาใหม่แล้วเข้ารหัสด้วย FFmpeg ไม่ต้องใช้ฟิลเตอร์เสริม `drawtext`, `ass` หรือ `subtitles`

## ข้อจำกัดสำคัญ

เมทาดาทาที่วัดได้ ผล OCR การ fit สไตล์และสมมติฐานวิธีตัดต่อเป็นหลักฐานคนละประเภท วิดีโอที่รวมชั้นแล้วไม่บอกได้แน่นอนว่าใช้คลิปต้นฉบับ เลเยอร์ที่ถูกบัง ฟอนต์ ปลั๊กอิน โปรเจกต์ editor หรือพรอมป์ต์ AI ใด ขอบเขตเริ่มต้นเน้นเวลา คำบรรยายและส่วนประกอบ 2D ที่รองรับ ยังไม่ใช่ตัวถอดวิดีโอสากลหรือผลิตภัณฑ์ที่พิสูจน์แล้วว่าดีที่สุด ความบังซ้อนซับซ้อน การสร้าง 3D, HDR mastering และ NLE round trip แบบใดก็ได้อยู่นอกขอบเขตตรวจสอบ อักษรซับซ้อนต้องมี shaping และทดสอบเฉพาะ การแปล README เก้าภาษาไม่ได้รับรอง OCR/การเรนเดอร์เก้าภาษา

ตรวจวิดีโอ B ตามเนื้อหาใหม่ ข้อตกลงสไตล์และการเล่น ไม่ใช้ความเหมือนพิกเซลทั้งเฟรมกับ A การตรวจเชิงเทคนิคแยกจากการตัดสินคุณภาพสร้างสรรค์ของคน [หลักฐานและข้อจำกัด (English)](docs/VALIDATION.md)

## ประมวลผลในเครื่องและเครดิต

แกนหลักทำงานในเครื่อง ไม่ต้องมี API แบบเสียเงิน ไม่อัปโหลดวิดีโอไปยัง inference ที่โฮสต์ และไม่เผยแพร่สื่ออัตโนมัติ การติดตั้ง dependencies หรือใช้ provider เสริมอาจเชื่อมต่อเครือข่าย นโยบาย Claude/Codex host แยกต่างหาก [Privacy (English)](docs/PRIVACY.md) ได้แรงบันดาลใจจาก JuneYaooo/rea-video เป็นผลิตภัณฑ์อิสระ ไม่ใช่รุ่นอัปเกรดทางการ เงื่อนไขโค้ด ฟอนต์ สื่อ โคเดกและโมเดลใช้แยกกัน

รายงาน local จะคัดลอกสื่ออ้างอิงและหลักฐานตามค่าเริ่มต้น `report --no-media` ละเว้นเฉพาะสำเนาสื่อเต็ม แต่ยังมีข้อความ OCR เส้นทาง local และภาพ crop โปรดตรวจสอบก่อนแชร์

[การสนับสนุน (English)](SUPPORT.md) · [การดูแล (English)](docs/MAINTENANCE.md) · ไม่อ้างว่าคำแปลผ่านการตรวจแบบมืออาชีพโดยเจ้าของภาษา

[เสียงพูดในเครื่องและการเคลื่อนไหวขั้นสูง (เอกสารเทคนิคภาษาอังกฤษ)](skills/rea-video-pro-max/references/speech-and-motion.md).
