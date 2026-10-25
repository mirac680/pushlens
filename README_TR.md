# PushLens

**GitHub'a yüklemeden önce projenin içinde ne olduğunu gör.** PushLens, Git kurmadan GitHub'a dosya yüklemek isteyenler için yerel çalışan bir ön denetim aracıdır.

Önce proje klasörünü tara; olası API anahtarlarını, `.env` dosyalarını, üretilmiş klasörleri ve GitHub tarayıcı yükleme sınırlarını kontrol et. Kritik bir bulgu yoksa inceleyip GitHub'a yükleyebileceğin temiz bir ZIP hazırla.

**Git gerekmez. Hesap gerekmez. Yükleme yoktur. Ek çalışma zamanı paketi gerekmez.** PushLens seçtiğin klasörü yalnızca okur; kaynak dosyalarını değiştirmez.

## Hızlı başlangıç

Python 3.10 veya üstü gerekir. Tarayıcı sadece Python standart kütüphanesini kullanır; masaüstü arayüzü `tkinter` kullanır.

### Windows masaüstü uygulaması

1. Bu projeyi indirip ZIP'ten çıkar.
2. `Launch_PushLens.bat` dosyasına çift tıkla.
3. Proje klasörünü seç ve **Check project** düğmesine bas.
4. Bulguları incele. Kritik bulgu kalmadıysa **Create clean ZIP…** ile paketi oluştur.

Windows Python'ı bulamazsa [python.org](https://www.python.org/downloads/) adresinden Python kurarken **Add python.exe to PATH** seçeneğini işaretle. Masaüstü arayüzü için Tkinter içeren Python gerekir.

### Komut satırı

PushLens klasöründeki PowerShell'de:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m pushlens check "C:\projenin\bulundugu\klasor"
python -m pushlens pack "C:\projenin\bulundugu\klasor"
```

Tekrar kullanmak için kur (kurulumda setuptools derleme bağımlılığı kullanılır; uygulama çalışırken ek paket gerekmez):

```powershell
python -m pip install .
pushlens check "C:\projenin\bulundugu\klasor"
pushlens pack "C:\projenin\bulundugu\klasor"
```

ZIP varsayılan olarak proje klasörünün yanına `<klasör>-github-upload.zip` adıyla yazılır. İçinde en üstte bir proje klasörü bulunur. **GitHub'ın tarayıcı yükleyicisini kullanmadan önce ZIP'i çıkart**; aksi hâlde GitHub arşivi tek dosya olarak ekler.

## Denetlenenler

- `.env`, kimlik bilgisi/özel anahtar dosya adları ve yaygın AWS/GitHub/GitLab/Stripe token biçimleri. Eşleşen dosya içeriği hiçbir raporda yazdırılmaz.
- GitHub web arayüzünün tek seferde 100 dosya ve dosya başına 25 MiB sınırı.
- README, `.gitignore` ve lisans gibi eksik proje dosyaları.
- `.git`, sanal ortam, önbellek, `node_modules` ve derleme çıktısı gibi sık görülen üretilmiş dosyalar.
- Sembolik bağlantılar ve Windows dizin junction'ları takip edilmez; okunamayan veya 2 MiB üzerindeki metin dosyaları inceleme uyarısı verir.

Projeye özel hariç tutmalar için proje kökünde `.pushlensignore` adlı dosya oluştur; her satıra bir göreli yol veya glob yaz:

```gitignore
artifacts/
*.sqlite
customer-dump-*.csv
```

PushLens henüz `.gitignore` dosyasını yorumlamaz; GitHub'ın tarayıcı yükleyicisi de bu kuralları uygulamaz. Bir dosyanın yayımlanmasını istemiyorsan yolunu `.pushlensignore` dosyasına ekle, ZIP oluştur ve içeriğini incele.

## Gizlilik ve sınırlar

Tarama çevrimdışıdır; ağ isteği ve telemetri yoktur. Raporlarda dosya yolları, kural kodları ve satır numaraları bulunur; dosya içinden eşleşen sır değeri ya da kod parçası bulunmaz. Raporu paylaşmadan önce dosya adlarını incele. ZIP oluştururken geçici bir kopya taranır; kaynak proje değiştirilmez. Kritik bulgular ZIP oluşturmayı durdurur.

PushLens, sezgisel kurallarla çalışan bir kontrol listesidir; gizli bilgi bulunmayacağını garanti etmez. Desen taraması bazı anahtarları kaçırabilir veya sır olmayan metni sır sanabilir. GitHub'da yayımlamadan önce dosyaların tamamını ve ZIP'i kendin incele. PushLens ZIP'i Git geçmişinden ya da dosyanın başka kopyalarından sır silmez.

Kural kodları ve önerilen adımlar için [bulgu rehberine](docs/RULES.md) bakabilirsin.

Ayrıntılar: [Security & privacy](docs/SECURITY.md). Katkı için [CONTRIBUTING.md](CONTRIBUTING.md). MIT lisansı: [LICENSE](LICENSE).

GitHub repo açıklaması, konu etiketleri ve tarayıcıdan yükleme adımları için [Türkçe yayınlama rehberine](docs/GITHUB_YAYINLAMA.md) bak.

Gelecekte ele alınabilecek fikirler için [yol haritasını](ROADMAP.md) incele.
