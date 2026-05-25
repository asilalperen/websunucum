# MementOS - Kapsamlı Vibe Coding ve Yapay Zeka (AI) Geliştirme Günlüğü

Bu doküman, MementOS projesinin geliştirilme sürecinde yapay zeka asistanı (Antigravity / Gemini) ile yapılan etkileşimleri, analizleri ve mimari kararları kronolojik olarak detaylandırmaktadır. Proje, Bilişim Güvenliği ilkelerine ve ders (BLG106) gereksinimlerine tam uyumlu olacak şekilde, küçük adımlar (incremental steps) kuralına sadık kalınarak inşa edilmiştir.

---

### Oturum 1: Proje Temellerinin Atılması ve Flask Mimarisi
* **Tarih / Saat:** 22 Mayıs 2026 | 14:30 - 16:00
* **Odak Noktası:** Uygulama iskeletinin oluşturulması ve sanal ortam (venv) izolasyonu.
* **Süreç ve Analiz:** Projenin tek bir `app.py` dosyasına sıkışıp spagetti koda dönüşmemesi için yapay zekaya "Flask Factory Pattern ve Blueprint" mimarisi kurduruldu. Ortamın izole edilmesi için `requirements.txt` oluşturuldu. 
* **AI Yönlendirmesi (Prompt Stratejisi):** *"Bana MementOS adında bir Flask projesi iskeleti kur. Blueprint yapısı olsun ve SQLite veritabanı bağlansın."*
* **Kanıt:** ![Flask Kurulumu](img/[FOTO-1-ADINI-YAZ.png])

### Oturum 2: Veritabanı (ORM) Modelleri ve İlişkisel Kriz Yönetimi
* **Tarih / Saat:** 23 Mayıs 2026 | 11:15 - 13:45
* **Odak Noktası:** SQLAlchemy 2.x ile CRUD işlemleri, Tablo İlişkileri.
* **Süreç ve Analiz:** `User`, `Post` ve `Comment` tabloları arası One-to-Many ilişkiler kuruldu. Ancak testler sırasında bir kullanıcı silindiğinde, ona ait gönderilerin veritabanında "yetim (orphan)" kalarak sisteme hata verdirdiği tespit edildi (Foreign Key Constraint Fails).
* **AI Çözümü:** AI ile yapılan log analizinde ilişkilere `cascade="all, delete-orphan"` parametresi eklenmesi gerektiği anlaşıldı. Sorun `flask db migrate` ile çözüldü.
* **Kanıt:** ![Cascade Hatası Çözümü](img/[FOTO-2-ADINI-YAZ.png])

### Oturum 3: Mementgram Arayüzünün (UI/UX) Modernizasyonu
* **Tarih / Saat:** 23 Mayıs 2026 | 19:00 - 21:30
* **Odak Noktası:** Frontend estetiği, Flexbox kullanımı ve Card tasarımı.
* **Süreç ve Analiz:** Sistemin varsayılan form arayüzleri çok ilkeldi (dev butonlar, kayan inputlar). Projenin vizyonuna (Web OS) uyması için yapay zekaya katı CSS kuralları dikte edildi.
* **AI Yönlendirmesi (Prompt Stratejisi):** *"Devasa turuncu butonları sil. Mementgram akışını modern bir kart (.post-card) yapısına çevir. Üstte kullanıcı adı/avatar, altta yatay flexbox ile şık bir yorum inputu olsun."*
* **Kanıt:** ![Mementgram Modern UI](img/[FOTO-3-ADINI-YAZ.png])

### Oturum 4: Takip (Follow) Sistemi ve Keşfet Sekmesi
* **Tarih / Saat:** 24 Mayıs 2026 | 10:00 - 12:30
* **Odak Noktası:** Many-to-Many veritabanı ilişkisi ve Sosyal Ağ Dinamikleri.
* **Süreç ve Analiz:** Kullanıcıların birbirini takip edebilmesi için `followers` adında bir association (bağlantı) tablosu kuruldu. Mementgram arayüzüne JavaScript destekli "Global Akış" ve "Keşfet" sekmeleri (Tabs) eklendi.
* **AI Çözümü:** AI'a "Tek seferde devasa kod verme, sadece Takip et/Takipten çık backend rotalarını ve Keşfet sekmesini yap" şeklinde kısıtlayıcı (Manifesto) prompt verilerek hata yapması engellendi.

### Oturum 5: Bilişim Güvenliği Entegrasyonu (OTP ve 2FA Sistemi)
* **Tarih / Saat:** 24 Mayıs 2026 | 15:30 - 18:30
* **Odak Noktası:** Siber Güvenlik, Flask-Mail, SMTP ve Ortam Değişkenleri (.env).
* **Süreç ve Analiz:** Projenin bölüm gereksinimlerini karşılaması için standart şifrelemeye ek olarak E-posta ile Doğrulama (OTP) sistemi kuruldu. Kodun içine gömülü (hardcoded) şifreler `.env` dosyasına taşınarak izole edildi. `User` modeline `is_verified` ve `verification_code` sütunları eklendi.
* **AI Yönlendirmesi:** Yapay zekaya HTML şablonlu, sistem temasına uygun bir mail tasarımı yaptırıldı ve kullanıcı kayıt/giriş döngüsü 2 aşamalı hale (2FA) getirildi.
* **Kanıt:** ![OTP Mail Sistemi](img/[FOTO-4-ADINI-YAZ.png])

### Oturum 6: PDF Manifestosuna Uyum (Sayfalama ve LAN Desteği)
* **Tarih / Saat:** 25 Mayıs 2026 | 09:00 - 11:30
* **Odak Noktası:** Sistem optimizasyonu, Pagination ve Ağ paylaşımı.
* **Süreç ve Analiz:** İbrahim Hoca'nın PDF'inde yer alan "Liste sayfalarında pagination kullanılmalıdır" kuralı gereği, sunucuyu yoran `.limit(50)` sorguları tespit edilip iptal edildi. Yerine SQLAlchemy `.paginate()` yapısı kuruldu. Ayrıca uygulamanın ağdaki (LAN) diğer bilgisayarlardan test edilebilmesi için `app.run(host='0.0.0.0')` ayarı entegre edildi.
* **Kanıt:** ![Keşfet Sekmesi ve Pagination](img/[FOTO-5-ADINI-YAZ.png])

### Oturum 7: Masaüstü Deneyimi, Cursor Revizyonu ve Final Yayını
* **Tarih / Saat:** 25 Mayıs 2026 | 12:30 - 14:15
* **Odak Noktası:** İşletim sistemi hissiyatını (Web OS) güçlendirme, Git/GitHub sorun giderme.
* **Süreç ve Analiz:** Arayüzün standart bir site gibi hissettirmemesi için, şeffaf arka planlı özel imleçler (PNG Cursor) CSS dosyasına entegre edildi. 
* **Kriz Yönetimi:** Projenin GitHub'a aktarımı sırasında VS Code arayüzünün sonsuz döngüye (sync loop) girmesi üzerine arayüz terk edildi. Doğrudan terminal üzerinden `git add .`, `git commit` ve `git push -u origin main` komutlarıyla müdahale edilerek proje kaynak kodları Kozmik Kasa'ya (GitHub) hatasız şekilde mühürlendi.
* **Kanıt:** ![VS Code Git Terminal Çözümü](img/[FOTO-6-ADINI-YAZ.png])