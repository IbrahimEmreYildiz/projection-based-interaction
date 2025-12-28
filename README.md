<h1 align="center">PROJECTION BASED INTERACTION GAME</h1>

<p align="center">
  <b>Görüntü İşleme ve Karma Gerçeklik Tabanlı Etkileşim Projesi</b>
</p>

<div align="center">

| 👤 Geliştirici | 🎓 Öğrenci Numarası | 📚 Ders Adı |
| :---: | :---: | :---: |
| **İbrahim Emre Yıldız** | **2020555069** | **Mixed-Reality** |

</div>

<br>

## 📝 Proje Özeti
Bu proje, **Bilgisayar Görüsü (Computer Vision)** teknikleri kullanılarak geliştirilmiş, **temassız (touchless)** ve **projeksiyon tabanlı** bir Karma Gerçeklik (Mixed Reality) oyunudur. 

Kullanıcı, fiziksel bir yüzeye (ekran veya duvar) yansıtılan sanal nesnelerle, herhangi bir giyilebilir sensör, eldiven veya kumanda olmadan **sadece el hareketleriyle** etkileşime geçer.

## 🚀 Temel Özellikler

* **🖐️ Gelişmiş El Takibi:** MediaPipe kütüphanesi ile yüksek performanslı el ve parmak ucu tespiti.
* **📐 Perspektif Düzeltme (Homography):** Kamera açısı ne kadar yamuk olursa olsun, 4 noktalı kalibrasyon sistemi ile oyun alanı düzeltilir ve koordinatlar mükemmel eşlenir.
* **🎲 3D Görselleştirme:** OpenCV kullanılarak sıfırdan çizilen 3 boyutlu tel kafes (wireframe) küpler.
* **🔄 Hibrit İçerik Yönetimi:**
    * **Animasyon Desteği:** Dalgalanan bayraklar gibi sıralı PNG dosyalarını oynatabilme.
    * **Statik Obje Desteği:** Sabit resimleri (hayvanlar vb.) 3D küplerin içine doku olarak giydirme.
* **🎛️ İnteraktif Menü Sistemi:** El hareketleriyle kontrol edilen, "Bayrak Modu" ve "Hayvan Modu" arasında geçiş sağlayan sanal arayüz.


Project_Root/
│
├── main.py                # Ana proje kodu
├── README.md              # Proje dokümantasyonu
└── 3d_frames/             # Oyun Varlıkları (Assets)
    ├── flags/             # Bayrak animasyon kareleri (0.png, 1.png...)
    └── animals/           # Hayvan resimleri (bear.png, elephant.png...)



## 🎮 Nasıl Oynanır?

### 1. Donanım Kurulumu
* Bilgisayar ekranını bir duvara yansıtın veya laptop ekranını kullanın.
* Harici bir kamerayı (veya Iriun Webcam yüklü telefonu), ekranı tamamen görecek şekilde karşısına yerleştirin.
* **Önemli:** Kamera ekranı görmeli, eliniz ise kamera ile ekran arasına girmelidir.

### 2. Kalibrasyon (Kritik Adım)
Oyun başladığında kamera görüntüsü üzerinde ekranın **4 köşesini** şu sırayla tıklayın:
1.  **Sol Üst**
2.  **Sağ Üst**
3.  **Sağ Alt**
4.  **Sol Alt**

*(Not: Sıralama saat yönündedir. Yanlış yapılırsa oyun ters çalışır.)*

### 3. Oyun Modları
Kalibrasyon bittiğinde Menü Ekranı açılır:
* **🇹🇷 Bayraklar Modu:** Havada asılı duran "BAYRAKLAR" butonuna elinizle dokunun. Küplerin içinde dalgalanan ülke bayraklarını yakalayın.
* **🐘 Hayvanlar Modu:** "HAYVANLAR" butonuna dokunun. Küplerin içindeki hayvanları yakalayın.

*Not: Menüye dönmek için klavyeden `M` tuşuna, çıkmak için `Q` tuşuna basabilirsiniz.*

## 🧠 Teknik Detaylar (Algoritma)

Proje, **Koordinat Eşleme (Coordinate Mapping)** prensibine dayanır:

1.  **Görüntü İşleme:** Kamera görüntüsü alınır ve kullanıcı deneyimi için aynalanır (Mirroring).
2.  **Matris Hesaplama:** Seçilen 4 nokta ile `cv2.getPerspectiveTransform` kullanılarak bir dönüşüm matrisi oluşturulur.
3.  **Konum Tespiti:** MediaPipe ile parmak ucunun (X, Y) koordinatları tespit edilir.
4.  **Warping (Dönüşüm):** `cv2.perspectiveTransform` fonksiyonu ile kameradaki parmak konumu, oyun ekranındaki (sanal dünyadaki) piksel karşılığına çevrilir.
5.  **Etkileşim:** Dönüştürülmüş parmak koordinatları ile sanal objelerin koordinatları çakışırsa (Collision Detection), etkileşim gerçekleşir.


## 🛠️ Kurulum ve Gereksinimler

Projenin çalışması için Python yüklü olmalıdır. Gerekli kütüphaneleri aşağıdaki komutla yükleyebilirsiniz:

```bash
pip install opencv-python mediapipe numpy
