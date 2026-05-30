# Yapay Zeka Etkileşim Günlüğü (AI Günlüğü)

Bu doküman, MementOS projesinin geliştirilme sürecinde Baş Yapay Zeka Asistanı ile yapılan etkileşimleri (Vibe Coding), yaşanılan krizleri, uygulanan çözümleri ve yönlendirme (prompt) süreçlerini tarihsel bir sırayla özetlemektedir.

---

### Oturum 1: Temel Flask ve Blueprint Kurulumu
**Odak Noktası:** Uygulamanın iskeletinin oluşturulması.  
**Süreç & Yönlendirmeler:**  
Projeye büyük bir monolitik dosya ile başlamak yerine, asistandan projeyi "Application Factory" desenine uygun şekilde bölmesini (auth, main, errors klasörleri) ve Blueprint yapısını kurmasını istedim. Flask altyapısı ve temel `__init__.py` dosyaları bu oturumda saniyeler içinde oluşturuldu. Asistanın terminal araçlarını kullanarak dizinleri bizzat oluşturması projeye hızlı bir ivme kazandırdı.
<br>
[BURAYA_GORSEL_GELECEK_1.png]

---

### Oturum 2: Veritabanı (Cascade Delete) Krizinin Çözümü
**Odak Noktası:** SQLAlchemy Foreign Key kısıtlamaları ve silme hataları.  
**Süreç & Yönlendirmeler:**  
Kullanıcıları silmeye çalıştığımızda veya bir anıyı veritabanından uçururken "IntegrityError" patlamaları yaşadık. Yorumlar, gönderiler ve kullanıcılar birbirine sıkı sıkıya bağlı olduğu için manuel silme mümkün değildi. Hata logunu doğrudan asistana kopyalayıp, modellerdeki ilişkilere `cascade="all, delete-orphan"` ve veritabanı migrate ayarlarındaki kısıtlamaları eklemesini istedim. Sorun Alembic (Flask-Migrate) üzerinden kalıcı olarak çözüldü.
<br>
[BURAYA_GORSEL_GELECEK_2.png]

---

### Oturum 3: Mementgram UI (Kart Yapısı, Flexbox)
**Odak Noktası:** İşletim sistemi pencereleri ve Mementgram akış tasarımı.  
**Süreç & Yönlendirmeler:**  
Backend sorunsuzdu ancak frontend çok basitti. Asistana "Sıradan bir site istemiyorum, Windows gibi pencereleri olan ve tıklanınca Modal açılan bir masaüstü (Desktop) ortamı kodla" talimatını verdim. Vanilla CSS, Flexbox ve Glassmorphism kullanılarak Mementgram, Galeri ve Anı Odası pencereleri tasarlandı. Özellikle gönderi (post) kartlarının "action butonları" (beğen, yorum) hizalamalarında AI'a ciddi CSS yönlendirmeleri yapıldı.
<br>
[BURAYA_GORSEL_GELECEK_3.png]

---

### Oturum 4: LAN Erişimi (0.0.0.0) ve Global Akış Entegrasyonu
**Odak Noktası:** Aynı ağdaki cihazlardan erişim ve çoklu test.  
**Süreç & Yönlendirmeler:**  
Telefonumdan siteye bağlanarak Mementgram uygulamasında paylaşım testleri yapmak istiyordum. Ancak localhost (`127.0.0.1`) dışarıya kapalıydı. Asistandan projeyi `0.0.0.0` üzerinden ayağa kaldırmasını ve firewall ayarlarında sorun olmaması için portu `5000`'de sabitlemesini istedim. Telefonda yaptığım paylaşımın PC tarayıcısına anında düştüğünü görmek, Mementgram Global Akışının başarıyla entegre edildiğini kanıtladı.
<br>
[BURAYA_GORSEL_GELECEK_4.png]

---

### Oturum 5: 2FA, Flask-Mail SMTP Kurulumu ve Terminal Fallback (B Planı) İcadı
**Odak Noktası:** Mail doğrulama ve iletişim kriz senaryoları.  
**Süreç & Yönlendirmeler:**  
Şifre sıfırlama sistemi için SMTP bilgilerini `.env` üzerine kurduk. Ancak internetin kesik olduğu veya Gmail'in SMTP'yi reddettiği durumlarda uygulamanın çökmesi büyük bir problemdi. Asistana "Fail-safe bir mantık yaz, mail gitmezse bile şifre kodunu terminale 'print' etsin ki ben kopyalayıp girebileyim" diyerek Terminal Fallback sistemini icat ettik. Bu sayede local geliştirme ortamı pürüzsüz hale geldi.
<br>
[BURAYA_GORSEL_GELECEK_5.png]

---

### Oturum 6: Giriş Sisteminde "Beni Hatırla" Çerez Yönetimi
**Odak Noktası:** Session tutarlılığı ve Remember-Me yapısı.  
**Süreç & Yönlendirmeler:**  
Flask-Login entegrasyonu tamamlanmıştı ancak tarayıcıyı her kapattığımda tekrar login olmam gerekiyordu. Giriş ekranına bir checkbox koydurarak asistandan "Remember Me" mantığını Flask-Login dökümantasyonuna uygun olarak backende bağlamasını istedim. Çerezlerin (cookies) yönetimi ve session sürelerinin ayarlanması sorunsuz tamamlandı.
<br>
[BURAYA_GORSEL_GELECEK_6.png]

---

### Oturum 7: State Management İle Güvenli Profil/Şifre Güncelleme Döngüsü
**Odak Noktası:** Şifre değişimi sonrası kullanıcıyı Logout olmaktan kurtarmak.  
**Süreç & Yönlendirmeler:**  
Kullanıcı profil sekmesinden şifresini başarıyla değiştirdiğinde sistem güvenlik gereği hash uyuşmazlığından dolayı kişiyi dışarı atıyordu. Asistana, Flask'teki `session` mekanizmasını güncelleyerek kullanıcının session state'ini arka planda tazeleyen (logout yapmayan) bir mantık geliştirmesini istedim. Bu küçük detay UX (kullanıcı deneyimi) açısından çok tatmin edici bir dokunuş oldu.
<br>
[BURAYA_GORSEL_GELECEK_7.png]

---

### Oturum 8: Sayfalama (Pagination) ve Takipçi (Follow) Sistemi
**Odak Noktası:** Veri yönetimi ve sosyal ağ algoritmaları.  
**Süreç & Yönlendirmeler:**  
Mementgram kısmında çok fazla post olduğunda sayfanın çökmesini engellemek için Flask-SQLAlchemy'nin `.paginate()` fonksiyonu entegre edildi. Ayrıca asistandan, "Keşfet" kısmında diğer kullanıcıları listelemesini, Follow/Unfollow yetenekleri eklemesini istedim. "Takip ettiklerimin anılarını ayrı bir Akış'ta göster" diyerek veri manipülasyonunu başarıyla kurguladık.
<br>
[BURAYA_GORSEL_GELECEK_8.png]

---

### Oturum 9: Sistem Güvenlik Röntgeni (Security Audit) ve CSRF ile SECRET_KEY Zafiyetlerinin Yamanması
**Odak Noktası:** Siber Güvenlik testleri ve son rötuşlar.  
**Süreç & Yönlendirmeler:**  
Projenin bitimine doğru asistandan kendisini bir siber güvenlik uzmanı gibi düşünmesini ve kodu 6 farklı kategoride incelemesini (SQL Injection, CSRF, Password Hashing vs.) emrettim. Rapor, raw `<form>` taglarında CSRF (Cross-Site Request Forgery) korumasının eksik olduğunu gösterdi. Hemen asistana, `EmptyForm` sınıfı oluşturarak tüm sayfalardaki Beğen, Sil, Takip Et butonlarına `{{ empty_form.hidden_tag() }}` eklemesi yönünde "Vibe Coding" talimatı verdim ve sistemin güvenlik açıklarını başarıyla yamadık.
<br>
[BURAYA_GORSEL_GELECEK_9.png]