# MementOS Proje Raporu

## 1. Projenin Amacı ve Vizyonu
MementOS, kullanıcılara standart bir web sitesinde gezinmek yerine tarayıcı üzerinden bir işletim sistemi (Web OS) deneyimi sunmayı hedefleyen kapsamlı bir dönem sonu projesidir. Masaüstü ikonları, pencereli klasör yapıları ve özellikle kendi içinde barındırdığı "Mementgram" isimli sosyal ağ ile dinamik bir yapıya sahiptir.

## 2. Kullanılan Teknolojiler ve Mimari
Projenin backend tarafında **Python** ve **Flask** framework'ü kullanılmıştır. Kodların sürdürülebilir olması için Blueprint yapısı (Factory Pattern) tercih edilmiştir. 
Veritabanı olarak **SQLite** ve ORM aracı olarak **SQLAlchemy 2.x** kullanılmıştır. Tablolar arası karmaşık ilişkiler (One-to-Many ve Many-to-Many), `followers` ve `likes` gibi yapılarla desteklenmiştir. Frontend tarafında ise Jinja2 şablon motoru, HTML5, CSS3 (Flexbox/Grid mimarileri) ve arayüz etkileşimleri için Vanilla JavaScript kullanılmıştır.

## 3. Güvenlik Altyapısı (Bilişim Güvenliği Vizyonu)
Bilişim Güvenliği Teknolojisi bölümü öğrencisi olmamın getirdiği vizyonla, standart şifreleme (Werkzeug password_hash) sistemine ek olarak projeye **2 Aşamalı Doğrulama (2FA)** entegre edilmiştir.
Kullanıcı kayıt olurken veya güvenlik ayarlarından 2FA'yı aktif ettiğinde, Google SMTP sunucuları üzerinden (Flask-Mail kütüphanesi yardımıyla) kullanıcının e-posta adresine 6 haneli bir OTP (Doğrulama Kodu) fırlatılmaktadır. Sistemdeki mail şifreleri gibi kritik veriler `.env` dosyası içerisinde izole edilerek GitHub üzerinde ifşa olması (leak) engellenmiştir.

## 4. Yapay Zeka ile Geliştirme (Vibe Coding) Deneyimi
Bu proje büyük ölçüde "Vibe Coding" mantığı ile, yapay zeka asistanları (Gemini / Cursor / Antigravity) yönlendirilerek kodlanmıştır. Süreç boyunca yapay zekaya devasa kod blokları yazdırmak (Anti-Pattern) yerine, sistem modüller halinde (önce veritabanı, sonra arayüz, en son SMTP) parçalanarak inşa edilmiştir.

Örneğin, Mementgram arayüzü kurulurken doğrudan "Bana bir sosyal medya yap" demek yerine, "Gönderi kartlarını flexbox ile hizala, yorumları yatay bir düzene oturt" gibi spesifik, mimariye yönelik promptlar verilmiştir. Alınan terminal hataları (özellikle veritabanı migrasyonlarında yaşanan cascade çatışmaları) log okuma yöntemiyle AI'a sunulmuş ve hızlı çözümler üretilmiştir.

## 5. Karşılaşılan Zorluklar ve Çözümler
* **Sayfalama (Pagination) Adaptasyonu:** İlk aşamada veritabanı sorguları `.limit(50)` gibi kısıtlamalarla yapılıyordu. Hoca gereksinimleri (PDF) incelendikten sonra mimari baştan aşağı revize edilerek Flask-SQLAlchemy'nin `.paginate()` fonksiyonuna geçirildi.
* **Bağımlılık (Dependency) Sorunları:** Geliştirme ortamındaki paketlerin çakışması, sanal ortam (venv) kullanılarak ve `requirements.txt` dosyasının düzenli güncellenmesiyle çözüldü.
* **Mobil Uyumluluk vs. İşletim Sistemi Hissiyatı:** Arayüzün bir işletim sistemini simüle etmesi amaçlandığı için mobil cihazlarda görünüm zorlukları yaşandı. Bu durum, masaüstü (Desktop-first) tasarım felsefesine sadık kalınarak, CSS grid yapılarıyla olabildiğince optimize edildi.

## 6. Sonuç
MementOS, CRUD işlemlerini başarıyla gerçekleştiren, modern sosyal ağ dinamiklerini (Takip, Beğeni, Yorum) barındıran, 2FA güvenlik altyapısına sahip ve yapay zeka entegrasyonuyla geliştirilmiş sağlam bir Web OS simülasyonu olarak tamamlanmıştır.