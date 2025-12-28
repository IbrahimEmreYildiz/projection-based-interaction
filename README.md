Projeksiyon Tabanlı Etkileşim Oyunu (Projection-Based Interaction Game)
Bu proje, bilgisayar görüsü (Computer Vision) teknikleri kullanılarak geliştirilmiş, temassız (touchless) ve projeksiyon tabanlı bir Karma Gerçeklik (Mixed Reality) oyunudur. Kullanıcı, fiziksel bir yüzeye (ekran veya duvar) yansıtılan sanal nesnelerle, herhangi bir giyilebilir sensör veya kumanda olmadan sadece el hareketleriyle etkileşime geçer.

🎯 Proje Özeti
Geliştirici: İbrahim Emre Yıldız

Teknolojiler: Python, OpenCV, MediaPipe, NumPy

Temel Mekanik: Homography (Perspektif Düzeltme) ve El Takibi (Hand Tracking)

🚀 Özellikler
Gelişmiş El Takibi: MediaPipe kütüphanesi ile milisaniyelik hızda el ve parmak ucu tespiti.

Perspektif Düzeltme (Homography): Kamera açısı ne kadar yamuk olursa olsun, 4 noktalı kalibrasyon sistemi ile oyun alanı düzeltilir ve koordinatlar mükemmel eşlenir.

3D Görselleştirme: OpenCV kullanılarak çizilen 3 boyutlu tel kafes (wireframe) küpler.

Hibrit İçerik Yönetimi:

Animasyon Desteği: Dalgalanan bayraklar gibi sıralı PNG dosyalarını oynatabilme.

Statik Obje Desteği: Sabit resimleri (hayvanlar vb.) 3D küplerin içine doku (texture) olarak giydirme.

Menü Sistemi: El hareketleriyle kontrol edilen, "Bayrak Modu" ve "Hayvan Modu" arasında geçiş sağlayan interaktif arayüz.

🛠️ Kurulum
Projeyi çalıştırmak için aşağıdaki kütüphanelerin yüklü olması gerekir:

Bash

pip install opencv-python
pip install mediapipe
pip install numpy
📂 Dosya Yapısı
Projenin düzgün çalışması için klasör yapısı aşağıdaki gibi olmalıdır:

Plaintext

Project_Root/
│
├── main.py                # Ana oyun kodu
├── README.md              # Proje dokümantasyonu
└── 3d_frames/             # Oyun varlıkları (Assets)
    ├── flags/             # Bayrak animasyon kareleri (0.png, 1.png...)
    └── animals/           # Hayvan resimleri (bear.png, elephant.png...)
🎮 Nasıl Oynanır?
1. Donanım Kurulumu
Bilgisayar ekranını bir duvara yansıtın veya laptop ekranını kullanın.

Harici bir kamerayı (veya Iriun Webcam yüklü telefonu), ekranı tamamen görecek şekilde karşısına yerleştirin.

Önemli: Kamera sizi değil, ekranı çekmelidir. Eliniz kamera ile ekran arasına girmelidir.

2. Kalibrasyon (Çok Önemli!)
Oyun başladığında kamera görüntüsü üzerinde ekranın 4 köşesini sırasıyla işaretleyin:

Sol Üst

Sağ Üst

Sağ Alt

Sol Alt

(Sıralama saat yönündedir. Yanlış yapılırsa oyun ters çalışır.)

3. Oyun Modları
Kalibrasyon bittiğinde Menü Ekranı açılır:

Bayraklar Modu: Havada asılı duran "BAYRAKLAR" butonuna elinizle dokunun. Küplerin içinde dalgalanan ülke bayraklarını yakalamaya çalışın.

Hayvanlar Modu: "HAYVANLAR" butonuna dokunun. Küplerin içindeki hayvanları yakalayın.

Not: Menüye dönmek için klavyeden M tuşuna, çıkmak için Q tuşuna basabilirsiniz.

🧠 Teknik Detaylar (Algoritma)
Proje, Koordinat Eşleme (Coordinate Mapping) prensibine dayanır.

Görüntü İşleme: Kamera görüntüsü alınır ve gerekirse (ayna etkisi için) ters çevrilir.

Kalibrasyon Matrisi: Seçilen 4 nokta ile cv2.getPerspectiveTransform kullanılarak bir dönüşüm matrisi oluşturulur.

Konum Tespiti: MediaPipe ile parmak ucunun (X, Y) koordinatları bulunur.

Dönüşüm (Warping): cv2.perspectiveTransform fonksiyonu ile kameradaki parmak konumu, oyun ekranındaki (sanal dünyadaki) konuma çevrilir.

Etkileşim: Eğer dönüştürülmüş parmak koordinatları, sanal küpün koordinatlarıyla çakışırsa (Collision Detection), puan kazanılır ve obje yer değiştirir.

Author: İbrahim Emre Yıldız

Year: 2025
