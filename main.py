import cv2  # Görüntü işleme kütüphanesi (OpenCV)
import numpy as np  # Matematiksel hesaplamalar ve matris işlemleri için
import mediapipe as mp  # Google'ın Yapay Zeka el takip kütüphanesi
import random  # Rastgele sayı üretimi (Küp konumları için)

# ==========================================
# 1. SİSTEM AYARLARI VE SABİTLER
# ==========================================
KAMERA_ID = 1  # Bilgisayara bağlı kameranın ID'si (0: Dahili, 1: Harici/Iriun)
OYUN_GENISLIK = 1000  # Sanal projeksiyon alanının genişliği (px)
OYUN_YUKSEKLIK = 700  # Sanal projeksiyon alanının yüksekliği (px)
OBJE_SAYISI = 5  # PDF Şartı: En az 4-5 dinamik nesne gerekliliği

# ==========================================
# 2. MEDIAPIPE EL TAKİP MODELİ KURULUMU
# ==========================================
mp_hands = mp.solutions.hands
# min_detection_confidence=0.7: %70 emin olmadan el var demez (Hata oranını düşürür)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils  # İskelet çizimi için yardımcı araç

# ==========================================
# 3. GLOBAL DEĞİŞKENLER
# ==========================================
kalibrasyon_noktalari = []  # Kameradan seçilen 4 köşe noktası (u, v)
kalibrasyon_tamamlandi = False  # Kalibrasyon durumu kontrolü
matris = None  # Homography (Dönüşüm) Matrisi
puan = 0  # Oyuncu skoru

# Hedef Objelerin Listesi (Her birinin X, Y koordinatı ve Rengi ayrı tutulur)
hedef_objeler = []

# Başlangıçta 5 adet rastgele konumda ve renkte obje üretimi
for _ in range(OBJE_SAYISI):
    hx = random.randint(100, OYUN_GENISLIK - 100)
    hy = random.randint(100, OYUN_YUKSEKLIK - 100)
    # Rastgele RGB renk üretimi (Parlak renkler tercih edildi)
    color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
    hedef_objeler.append({'x': hx, 'y': hy, 'c': color})


# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================

def fare_tiklama(event, x, y, flags, param):
    """
    Kullanıcının kamera görüntüsü üzerinde 4 köşe seçmesini sağlar.
    Bu noktalar, perspektif düzeltme (Homography) için 'Kaynak Noktalar' olacaktır.
    """
    global kalibrasyon_noktalari
    if event == cv2.EVENT_LBUTTONDOWN and not kalibrasyon_tamamlandi:
        kalibrasyon_noktalari.append((x, y))
        print(f"Kalibrasyon Noktasi {len(kalibrasyon_noktalari)} Secildi: {x}, {y}")


def draw_3d_cube(img, center, size, color):
    """
    2D görüntü üzerinde 3D tel kafes (wireframe) küp çizer.
    PDF Şartı: '3D Visualization' gereksinimini karşılar.
    """
    cx, cy = center
    r = size // 2  # Yarıçap
    depth = size // 3  # Derinlik hissi için piksel kaydırma miktarı

    # Küpün Ön Yüzü (Kare)
    front = np.array([
        [cx - r, cy - r], [cx + r, cy - r],
        [cx + r, cy + r], [cx - r, cy + r]
    ], np.int32)

    # Küpün Arka Yüzü (Perspektif için kaydırılmış kare)
    back = np.array([
        [cx - r + depth, cy - r - depth], [cx + r + depth, cy - r - depth],
        [cx + r + depth, cy + r - depth], [cx - r + depth, cy + r - depth]
    ], np.int32)

    # Yüzleri çiz
    cv2.polylines(img, [front], True, color, 3)  # Ön yüz kalın
    cv2.polylines(img, [back], True, color, 1)  # Arka yüz ince

    # Köşeleri birleştirerek 3D derinlik çizgilerini oluştur
    for f, b in zip(front, back):
        cv2.line(img, tuple(f), tuple(b), color, 1)


# ==========================================
# 5. ANA PROGRAM DÖNGÜSÜ
# ==========================================
cap = cv2.VideoCapture(KAMERA_ID)

# Pencereleri oluştur
cv2.namedWindow("Goz (Telefon)")
cv2.setMouseCallback("Goz (Telefon)", fare_tiklama)  # Fare olaylarını bağla
cv2.namedWindow("Oyun Alani", cv2.WINDOW_NORMAL)  # Boyutlandırılabilir pencere

print("--- SISTEM BASLATILDI ---")
print("ADIM 1: Telefon kamerasindan 'Oyun Alani' penceresini gör.")
print("ADIM 2: 'Goz' penceresinde oyun alanının 4 kösesine tıkla.")

while True:
    success, img = cap.read()
    if not success:
        print("Kamera verisi alınamıyor! Bağlantıyı kontrol edin.")
        break

    # ---------------------------------------------------------
    # MOD 1: KALİBRASYON (HOMOGRAPHY HESAPLAMA)
    # ---------------------------------------------------------
    if not kalibrasyon_tamamlandi:
        # Kullanıcıya görsel geri bildirim
        cv2.putText(img, f"Kalibrasyon: {len(kalibrasyon_noktalari)}/4 (Koseleri Sec)",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Seçilen noktaları işaretle
        for pt in kalibrasyon_noktalari:
            cv2.circle(img, pt, 5, (0, 255, 0), -1)

        # 4 Nokta seçildiyse Matrisi Hesapla
        if len(kalibrasyon_noktalari) == 4:
            # 1. Kaynak Noktalar (Kameradan gelen yamuk görüntü koordinatları)
            src_pts = np.float32(kalibrasyon_noktalari)

            # 2. Hedef Noktalar (Düzeltilmiş ekranın tam köşe koordinatları)
            dst_pts = np.float32([
                [0, 0],
                [OYUN_GENISLIK, 0],
                [OYUN_GENISLIK, OYUN_YUKSEKLIK],
                [0, OYUN_YUKSEKLIK]
            ])

            # 3. Perspektif Dönüşüm Matrisini Çıkar (Homography Matrix)
            matris = cv2.getPerspectiveTransform(src_pts, dst_pts)
            kalibrasyon_tamamlandi = True
            print("Kalibrasyon Basarili! Oyun Moduna Geciliyor...")

    # ---------------------------------------------------------
    # MOD 2: OYUN VE ETKİLEŞİM (INTERACTION LOOP)
    # ---------------------------------------------------------
    else:
        # Siyah arka plan oluştur (Projektör mantığı için siyah = ışık yok)
        oyun_ekrani = np.zeros((OYUN_YUKSEKLIK, OYUN_GENISLIK, 3), dtype=np.uint8)

        # MediaPipe RGB formatı ister, dönüşüm yapıyoruz
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)

        detected_pos = None  # Tespit edilen parmağın oyun dünyasındaki konumu

        # El tespiti yapıldıysa
        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # İskeleti kamera görüntüsüne çiz (Debug amaçlı)
                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

                # İşaret Parmağı Ucunu Al (Landmark ID 8)
                index_finger = hand_lms.landmark[8]
                h, w, c = img.shape
                # Normalize edilmiş (0-1 arası) koordinatları piksele çevir
                cx, cy = int(index_finger.x * w), int(index_finger.y * h)

                # Kamerada parmağı işaretle
                cv2.circle(img, (cx, cy), 10, (255, 0, 255), -1)

                # --- KRİTİK AŞAMA: KOORDİNAT DÖNÜŞÜMÜ (MAPPING) ---
                # Kamera koordinatlarını (cx, cy), Homography matrisi ile
                # Oyun Dünyası koordinatlarına (game_x, game_y) çeviriyoruz.
                pts = np.array([[[cx, cy]]], dtype='float32')
                warped_pt = cv2.perspectiveTransform(pts, matris)[0][0]

                detected_pos = (int(warped_pt[0]), int(warped_pt[1]))

                # Oyunda sanal imleci çiz (Kırmızı Daire)
                cv2.circle(oyun_ekrani, detected_pos, 20, (0, 0, 255), -1)

        # --- ÇOKLU OBJE YÖNETİMİ VE ÇARPIŞMA (COLLISION) ---
        for obje in hedef_objeler:
            # Objeyi çiz
            draw_3d_cube(oyun_ekrani, (obje['x'], obje['y']), 80, obje['c'])

            # Etkileşim Kontrolü
            if detected_pos:
                # Mesafe Hesaplama (Öklid benzeri basit fark kontrolü)
                dx = abs(detected_pos[0] - obje['x'])
                dy = abs(detected_pos[1] - obje['y'])

                # Eğer parmak küpün merkezine 50px kadar yakınsa
                if dx < 50 and dy < 50:
                    puan += 1
                    # Küpü yeni rastgele bir konuma taşı
                    obje['x'] = random.randint(100, OYUN_GENISLIK - 100)
                    obje['y'] = random.randint(100, OYUN_YUKSEKLIK - 100)
                    # Rengini değiştir
                    obje['c'] = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        # Puan Durumunu Ekrana Yaz
        cv2.putText(oyun_ekrani, f"Puan: {puan}", (30, 60), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

        # Oluşturulan oyun ekranını göster
        cv2.imshow("Oyun Alani", oyun_ekrani)

    # Kamera görüntüsünü göster (Debug için)
    cv2.imshow("Goz (Telefon)", img)

    # 'q' tuşuna basılırsa çık
    if cv2.waitKey(1) == ord('q'): break

# Kaynakları serbest bırak
cap.release()
cv2.destroyAllWindows()