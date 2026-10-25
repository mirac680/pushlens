# PushLens'i GitHub'a yükleme

## Repo bilgileri

- **Repo adı:** `pushlens`
- **Açıklama:** `Check what goes into your GitHub upload before you publish. Offline, local, and Git-free.`
- **Topics:** `github`, `github-upload`, `beginner-friendly`, `python`, `privacy-first`, `offline-first`, `secret-scanning`, `open-source`
- **Lisans:** MIT (`LICENSE` dosyası hazır.)
- **README:** GitHub ana sayfası için İngilizce `README.md`; Türkçe rehber `README_TR.md`.

## Tarayıcıdan yükleme

1. GitHub'da **New repository** seçip `pushlens` adında boş bir repo oluştur. Repo oluştururken ikinci bir README, `.gitignore` veya lisans ekleme; bunlar proje klasöründe zaten var.
2. Proje ZIP'ini bilgisayarında aç. GitHub'a ZIP dosyasının kendisini değil, açtığın klasörün içindeki proje dosyalarını yükle.
3. Repo sayfasında **Add file → Upload files** seçeneğini aç. Proje içeriğini ekle; listede `README.md`, `LICENSE`, `.github`, `src`, `docs`, `.gitignore` ve `.pushlensignore` bulunduğunu kontrol et. Noktayla başlayan dosyalar görünmüyorsa Windows Gezgini'nde **Görünüm → Göster → Gizli öğeler** seçeneğini açıp tekrar ekle.
4. Commit mesajı alanına `Initial release: PushLens 1.0.0` yazıp yüklemeyi tamamla.
5. Herkesin keşfedip yıldız verebilmesini istiyorsan repo görünürlüğünü **Public** seç; Public repoları herkes görebilir, Private repoları yalnızca erişim verdiğin kişiler görebilir. Public yapmadan önce dosya listesini ve README önizlemesini kontrol et; gerçek API anahtarı, parola veya özel dosya olmadığını son kez doğrula.

GitHub tarayıcısından bir seferde en fazla 100 dosya ve dosya başına 25 MiB yüklenebilir. Tarayıcı `.gitignore` kurallarını kendiliğinden uygulamaz. PushLens ZIP'i bilinen önbellek/çıktı klasörlerini ve `.pushlensignore` ile belirttiğin yolları dışarıda bırakır; ZIP'i yüklemeden önce içeriğini yine de incele.

GitHub'ın güncel adımları için [dosyaları depoya yükleme rehberine](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository) bakabilirsin.

Repo görünürlüğünün ne anlama geldiğini [GitHub'ın görünürlük rehberinde](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories#about-repository-visibility) okuyabilirsin.
