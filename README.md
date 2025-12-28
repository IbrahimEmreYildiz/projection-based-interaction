<h1 align="center">PROJECTION BASED INTERACTION GAME</h1>

<p align="center">
  <b>Görüntü İşleme ve Karma Gerçeklik Tabanlı Etkileşim Projesi</b>
</p>

<div align="center">

| 👤 Geliştirici | 🎓 Öğrenci Numarası | 📚 Ders Adı |
| :---: | :---: | :---: |
| **İbrahim Emre Yıldız** | **[2020555069]** | **[Mixed-Reality]** |

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

## 🛠️ Kurulum ve Gereksinimler

Projenin çalışması için Python yüklü olmalıdır. Gerekli kütüphaneleri aşağıdaki komutla yükleyebilirsiniz:

```bash
pip install opencv-python mediapipe numpy
