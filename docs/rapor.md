# MementOS: Mimari, Bilişim Güvenliği ve Vibe Coding Deneyim Raporu

**Proje Kapsamı:** Gazi Üniversitesi - BLG106 Dersi Proje Teslimi  
**Proje Adı:** MementOS  

Bu rapor, MementOS projesinin ardında yatan mimari kararları, "Vibe Coding" metodolojisiyle yapay zeka entegreli geliştirme süreçlerini ve uygulamanın Bilişim Güvenliği perspektifiyle nasıl inşa edildiğini detaylandırmak amacıyla hazırlanmıştır. 

## 1. MementOS Sistem Mimarisi ve İleri Düzey Yapılar

MementOS, Python temelli Flask web framework'ü kullanılarak, "Application Factory" deseni ve "Blueprint" mimarisiyle modüler olarak inşa edilmiştir. Sıradan bir web sitesi olmaktan ziyade, kullanıcıya "Web Tabanlı bir İşletim Sistemi" hissiyatı vermek üzere frontend'de HTML/CSS (Vanilla) tabanlı pencereli sistemler (OS Window) ve DOM manipülasyonları kullanılmıştır.

### 1.1 State Management (Durum Yönetimi) ve Güvenli Profil Güncelleme
Uygulamada kullanıcıların profil bilgilerini veya şifrelerini değiştirirken sistemden kopmamaları (logout olmamaları) kullanıcı deneyimi (UX) açısından kritik bir unsurdu. Klasik sistemlerde şifre değişimi oturumun kapanmasına neden olurken, MementOS'ta "State Management" mekanizması kullanılmıştır. Flask'in `session` yapısı ve Flask-Login eklentisi bir araya getirilerek; şifre değişim isteği onaylandığında veritabanında (SQLAlchemy) hash güncellenir ve kullanıcının `session` id'si anlık olarak yeni state ile eşitlenerek oturumun düşmesi (drop) engellenir.

### 1.2 Yerel Ağ İçi Erişim (0.0.0.0) ve Host Konfigürasyonu
Uygulama, standart `127.0.0.1` (localhost) yerine doğrudan `0.0.0.0` ağ arayüzü üzerinden ayağa kaldırılmıştır. Bu mimari karar sayesinde MementOS, çalıştığı sunucunun (veya yerel bilgisayarın) bağlı bulunduğu Wi-Fi/LAN ağındaki tüm cihazlardan, örneğin telefon veya tabletlerden, yerel IP adresi (örn. `192.168.1.x:5000`) üzerinden erişilebilir hale getirilmiştir. Bu özellik, Mementgram gibi sosyal akışların farklı cihazlardan eşzamanlı test edilmesine olanak tanımıştır. Zaman dilimi sorunları ise Windows üzerinde yerleşik `ZoneInfo` paketi hatalarından kaçınmak amacıyla statik `timedelta(hours=3)` ofseti ile Türkiye saatine kalibre edilerek güvenilir bir "local_time" filtresi ile aşılmıştır.

### 1.3 Terminal Fallback Sistemi (B Planı) Modülü
MementOS'un en dikkat çekici mimari çözümlerinden biri şüphesiz "Terminal Fallback" sistemidir. E-posta doğrulama (2FA) ve "Şifremi Unuttum" akışlarında Flask-Mail üzerinden SMTP kullanılarak e-postalar gönderilmektedir. Ancak production (canlı) ortamı dışındaki yerel testlerde veya sunucuda SMTP yapılandırma hataları (internet kesintisi, yanlış port vb.) yaşanabilme ihtimali göz önünde bulundurulmuştur. 
Bu senaryoda sistemin hata (Exception) fırlatıp çökmesi yerine, `try-except` bloklarıyla yakalanan SMTP hataları sonucu doğrulama kodları ve şifre sıfırlama linkleri doğrudan sunucu konsoluna (terminal) basılır (print edilir). Bu sayede geliştirici veya sistem yöneticisi loglardan kodu alıp süreci sekteye uğratmadan devam ettirebilir. Bu "Fail-Safe" yaklaşımı, uygulamanın dayanıklılığını (resilience) artırmaktadır.

---

## 2. Bilişim Güvenliği (Security Posture) Perspektifi

Uygulamanın çekirdek mimarisi, BLG106 dersinin kazanımlarından olan Bilişim Güvenliği prensipleri temel alınarak denetlenmiş (Security Audit) ve kodlanmıştır.

### 2.1 Şifre Saklama ve SQL Injection
Kullanıcıların en mahrem verilerinden olan şifreler veritabanına kesinlikle açık metin (plain text) olarak kaydedilmemektedir. `werkzeug.security` kütüphanesi yardımıyla `generate_password_hash` kullanılarak hashlenmekte ve doğrulama işlemleri `check_password_hash` ile yapılmaktadır. Uygulamadaki tüm veritabanı etkileşimleri SQLAlchemy ORM (Object Relational Mapping) aracılığıyla yapılmakta olup, hiçbir "raw SQL" sorgusu barındırmamaktadır. Bu durum uygulamayı SQL Injection saldırılarına karşı doğal bağışıklı hale getirir.

### 2.2 CSRF (Cross-Site Request Forgery) Zafiyetinin Yamanması
Projenin son evrelerinde yapılan güvenlik denetimlerinde, form içermeyen ve sadece buton tıklaması ile işlem yapan POST endpointlerinin (Örn: Beğeni Atma, Takip Etme, Anı Silme) sahte isteklerle sömürülebileceği tespit edilmiştir. Bu CSRF zafiyeti, `Flask-WTF` modülü üzerinden sadece gizli (hidden) bir CSRF token üreten ve input barındırmayan özel bir `EmptyForm` sınıfı yazılarak kapatılmıştır. Tüm şablonlardaki (index, user, post, feed) ilgili `<form>` etiketlerinin içerisine `{{ empty_form.hidden_tag() }}` enjekte edilmiş ve `routes.py` tarafında `form.validate_on_submit()` ile isteklerin kaynağı doğrulanarak zafiyet yamalanmıştır.

### 2.3 Çevresel Değişkenler (Environment Variables) ve SECRET_KEY
Sistemin güvenliği için hayati önem taşıyan `SECRET_KEY`, SMTP şifreleri ve veritabanı yolları kaynak koda gömülmek (hardcode) yerine `.env` dosyası üzerinden okunacak şekilde (python-dotenv ile) `config.py` içerisine entegre edilmiştir. Sürüm kontrol (Git) süreçlerinde `.env` dosyası `.gitignore`'a eklenerek açık kaynak sızıntılarının (data leak) önüne geçilmiştir.

---

## 3. Vibe Coding Deneyimi: Yapay Zeka Eşliğinde Geliştirme

Proje baştan sona geleneksel elle kodlama yönteminden çok "Vibe Coding" (Prompt Engineering tabanlı yapay zeka eşliğinde yazılım) prensibiyle ilerlemiştir. Projede baş yapay zeka asistanı olan Antigravity (Gemini tabanlı) ile interaktif, eşzamanlı ve iteratif bir geliştirme süreci yaşanmıştır.

Vibe Coding sürecinin en büyük avantajı, yapay zekanın sadece bana kod blokları vermesi değil, verdiğim sistem komutlarını anında yerel terminalimde çalıştırarak dosyaları manipüle edebilmesiydi. Bir hata (Traceback) aldığımda, hatayı okumak ve çözmek için zaman kaybetmek yerine terminal çıktısını doğrudan ajana sundum. Asistan, kendi yazdığı kodun yarattığı "cascade delete" gibi veri tutarsızlıklarını saniyeler içinde analiz edip projeyi ayağa kaldırmamı sağladı.

Ben bir "Yazılım Mimarı" şapkası giyerek vizyonu ve kuralları belirledim: "Bana bir Anı Odası klasörü ve Mementgram uygulaması yap. UI cam efekti (glassmorphism) olacak, responsive dizilecek" şeklindeki modüler promptlarımla frontend ve backend iş mantığını (Business Logic) asistanla paslaşarak hayata geçirdik. Hata ayıklama, güvenlik taramaları (audits) ve UI cilalamaları ile projenin kod satırlarından ziyade ürünün ruhuna (vibe) ve amacına odaklanma fırsatı buldum. Bu modern yazılım geliştirme metodolojisi, kısıtlı zamanda muazzam bir teknoloji yığınını (tech-stack) orkestra şefi gibi yönetmemi sağladı.