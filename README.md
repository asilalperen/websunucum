# MementOS 🖥️

**MementOS**, sıradan bir web sitesi olmanın ötesinde, kullanıcılarına eksiksiz bir "Web Tabanlı İşletim Sistemi (Web OS)" ve izole edilmiş bir dijital anı/sosyal ağ deneyimi sunmak amacıyla geliştirilmiş yenilikçi bir web uygulamasıdır. Kullanıcıların tamamen kendilerine ait, kişiselleştirilebilir bir masaüstü ortamında dijital günlüklerini tutmalarına ve "Mementgram" isimli global akış (feed) üzerinden diğer kullanıcılarla etkileşime girmelerine olanak tanır.

## 🚀 Projenin Vizyonu
MementOS, salt bir sosyal medya platformu değildir. Amacımız; kullanıcıya masaüstü hissiyatı veren pencereli (window tabanlı) bir arayüz, kişiselleştirilebilir arka planlar, temalar ve imleçler (cursor) eşliğinde, kendilerini özel bir sistemin içindeymiş gibi hissettirmektir. Hem kişisel bir galeri (Anı Odası) hem de topluluğa açık bir sosyal platformu (Mementgram) aynı ekosistem içerisinde, kesintisiz bir kullanıcı deneyimi ile harmanlar.

## ✨ Öne Çıkan Özellikler
- **Ağ İçi (LAN) Erişim (0.0.0.0):** Sistem sadece yerel makinede (localhost) değil, 0.0.0.0 üzerinden sunularak aynı yerel ağdaki (Wi-Fi/LAN) tüm cihazlardan (telefon, tablet vb.) sorunsuz şekilde erişilebilir olarak tasarlanmıştır.
- **Terminal Fallback Sistemi (B Planı):** "Şifremi Unuttum" veya e-posta ile bildirim süreçlerinde Flask-Mail SMTP yapısı kullanılır. Ancak sistemin kurulu olduğu sunucuda (veya yerel testlerde) internet kesintisi ya da yanlış SMTP konfigürasyonu olursa, sistem çökmez. Kodlar "Terminal Fallback" mekanizması ile sunucunun terminaline güvenli bir şekilde basılarak sürecin kesintisiz devam etmesi sağlanır.
- **Gelişmiş State Management:** Profil ve şifre güncellemelerinde kullanıcı çıkış yapmış (logout) durumuna düşürülmez. Session üzerinde aktif "state" tutularak, kullanıcıya hissettirilmeden arka planda güvenli geçişler sağlanır.
- **Çift Aşamalı Güvenlik ve "Beni Hatırla":** Giriş sistemlerinde güvenli çerez (cookie) yönetimi, remember-me mantığı ve kullanıcı tercihlerine dayalı şifreleme mekanizmaları mevcuttur.
- **Siber Güvenlik Standartları:** Secret Key, .env yönetimi, CSRF form doğrulamaları ve SQL Injection önlemleri gibi bilişim güvenliği prensipleri temel alınarak kodlanmıştır.

## 🛠️ Kurulum ve Ayağa Kaldırma (Docker)
Uygulamayı geliştirme ortamınızda veya sunucuda Docker ile çok hızlı bir şekilde ayağa kaldırabilirsiniz.

1. Proje dosyalarını bilgisayarınıza indirin ve dizine girin:
   ```bash
   git clone <repo-url>
   cd mementos
   ```

2. Ortam değişkenlerini (environment variables) ayarlamak için `.env` dosyasını oluşturun (Örnek yapılandırılmış `.env.example` dosyasını kullanabilirsiniz).
   ```bash
   cp .env.example .env
   ```

3. Docker Compose ile projeyi build edin ve başlatın:
   ```bash
   docker-compose up -d --build
   ```

4. Tarayıcınızdan `http://localhost:5000` veya yerel ağ IP'niz (örn: `http://192.168.1.x:5000`) üzerinden MementOS'a erişin.

## 📚 Dokümantasyon
- [Mimari ve Deneyim Raporu](docs/rapor.md)
- [Yapay Zeka Etkileşim Günlüğü](docs/ai-gunlugu.md)

Gazi Üniversitesi BLG106 Dersi kapsamında geliştirilmiştir.
