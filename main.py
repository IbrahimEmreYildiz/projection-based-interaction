import cv2  # Görüntü işleme kütüphanesi (OpenCV)
import numpy as np  # Matematik ve matris işlemleri
import mediapipe as mp  # Google'ın el takip kütüphanesi
import random  # Rastgele konum belirleme için
import os  # Dosya ve klasör işlemleri için

# ==========================================
# 1. AYARLAR VE SABİTLER
# ==========================================
KAMERA_ID = 1  # 1: Iriun/Harici Kamera, 0: Laptop Kamerası
OYUN_GENISLIK = 1000  # Yansıtılacak oyun ekranının genişliği (piksel)
OYUN_YUKSEKLIK = 700  # Yansıtılacak oyun ekranının yüksekliği (piksel)
OBJE_SAYISI = 5  # Ekranda aynı anda kaç küp olacak?
KUP_BOYUTU = 110  # 3D küplerin kenar uzunluğu

# Renk Ayarları (BGR Formatı)
ARKA_PLAN_RENGI = (255, 255, 255)  # Beyaz arka plan (Temiz görüntü için)
CIZGI_RENGI = (0, 0, 0)  # Siyah küp çizgileri

# Resimlerin olduğu klasör
KLASOR_ADI = "3d_frames"

# ==========================================
# 2. MEDIAPIPE (EL TAKİP) KURULUMU
# ==========================================
mp_hands = mp.solutions.hands
# min_detection_confidence=0.7: El olduğundan %70 eminse algılar (Hata payını azaltır)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# ==========================================
# 3. VARLIKLARI (ASSETS) YÜKLEME
# ==========================================
# Bu liste, oyun içinde kullanılacak tüm resim ve animasyonları tutar.
varlik_havuzu = []

print(f"--- '{KLASOR_ADI}' Klasöründen Varlıklar Yükleniyor ---")

if os.path.exists(KLASOR_ADI):
    # --- GRUP 1: TÜRK BAYRAĞI ANİMASYONU ---
    # 0.png, 1.png, 2.png dosyalarını sırayla okuyup bir animasyon dizisi oluşturur.
    tr_frames = []
    for isim in ["0.png", "1.png", "2.png"]:
        path = os.path.join(KLASOR_ADI, isim)
        # cv2.IMREAD_UNCHANGED: Resmi şeffaflık (Alpha kanalı) ile okur.
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            # Resmi küpün içine sığacak şekilde yeniden boyutlandır
            img = cv2.resize(img, (int(KUP_BOYUTU * 0.8), int(KUP_BOYUTU * 0.6)))
            tr_frames.append(img)

    # Eğer resimler bulunduysa havuza 'anim' (animasyon) tipiyle ekle
    if tr_frames:
        varlik_havuzu.append({'type': 'anim', 'data': tr_frames})
        print(f"Türk Bayrağı Animasyonu ({len(tr_frames)} kare) yüklendi.")

    # --- GRUP 2: KORE BAYRAĞI ANİMASYONU ---
    kr_frames = []
    for isim in ["k0.png", "k1.png", "k2.png"]:
        path = os.path.join(KLASOR_ADI, isim)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            img = cv2.resize(img, (int(KUP_BOYUTU * 0.8), int(KUP_BOYUTU * 0.6)))
            kr_frames.append(img)
    if kr_frames:
        varlik_havuzu.append({'type': 'anim', 'data': kr_frames})
        print(f"Kore Bayrağı Animasyonu ({len(kr_frames)} kare) yüklendi.")

    # --- GRUP 3: SABİT HAYVAN RESİMLERİ ---
    # Bunlar hareket etmez, tek karelik resimlerdir.
    for isim in ["elephant.png", "bear.png"]:
        path = os.path.join(KLASOR_ADI, isim)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            img = cv2.resize(img, (int(KUP_BOYUTU * 0.8), int(KUP_BOYUTU * 0.8)))
            # Hayvanları 'static' (sabit) tipiyle havuza ekle
            varlik_havuzu.append({'type': 'static', 'data': img})
            print(f"{isim} sabit resim olarak yüklendi.")

else:
    print(f"HATA: '{KLASOR_ADI}' klasörü bulunamadı! Lütfen oluşturun.")


# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================
def overlay_transparent(background, overlay, x, y):
    """
    PNG resimlerini şeffaflığını koruyarak arka plana yapıştırır.
    Alpha kanalı (4. kanal) kullanılarak matematiksel karışım yapılır.
    """
    bg_h, bg_w, _ = background.shape
    h, w, _ = overlay.shape

    # Taşma kontrolü: Resim ekran dışına çıkarsa kırpılır
    if x + w > bg_w: w = bg_w - x
    if y + h > bg_h: h = bg_h - y
    if x < 0 or y < 0: return background

    overlay = overlay[:h, :w]

    # Eğer resim şeffaf (4 kanallı) ise:
    if overlay.shape[2] == 4:
        alpha = overlay[:, :, 3] / 255.0  # Şeffaflık oranı (0.0 - 1.0 arası)
        for c in range(3):  # RGB kanallarını tek tek karıştır
            background[y:y + h, x:x + w, c] = (alpha * overlay[:, :, c] +
                                               (1 - alpha) * background[y:y + h, x:x + w, c])
    else:
        # Şeffaf değilse direkt yapıştır
        background[y:y + h, x:x + w] = overlay


def draw_3d_content_box(img, center, size, asset_info, frame_counter):
    """
    Ekrana 3 Boyutlu Tel Kafes (Wireframe) küp çizer ve içine resmi yerleştirir.
    Hem animasyonları hem de sabit resimleri yönetir.
    """
    cx, cy = center
    r = size // 2
    depth = size // 3  # Derinlik hissi vermek için kaydırma miktarı

    # Küpün Ön ve Arka Yüz Koordinatları Hesaplama
    front_pts = np.array([[cx - r, cy - r], [cx + r, cy - r], [cx + r, cy + r], [cx - r, cy + r]], np.int32)
    back_pts = np.array([[cx - r + depth, cy - r - depth], [cx + r + depth, cy - r - depth],
                         [cx + r + depth, cy + r - depth], [cx - r + depth, cy + r - depth]], np.int32)

    # 1. ADIM: Küpün Arka Yüzünü Çiz (İnce Çizgi)
    cv2.polylines(img, [back_pts], True, CIZGI_RENGI, 1)

    # 2. ADIM: İçeriği (Resim/Animasyon) Yerleştir
    img_to_draw = None
    if asset_info:
        if asset_info['type'] == 'static':
            # Sabit resimse direkt veriyi al
            img_to_draw = asset_info['data']
        elif asset_info['type'] == 'anim':
            # Animasyonsa, frame_counter'a göre sıradaki kareyi seç
            frames = asset_info['data']
            # Hız ayarı: (frame_counter // 5) ile animasyon hızını yavaşlatıyoruz
            idx = (frame_counter // 5) % len(frames)
            img_to_draw = frames[idx]

    # Resmi küpün ortasına yerleştir
    if img_to_draw is not None:
        img_x = cx - (img_to_draw.shape[1] // 2) + (depth // 2)
        img_y = cy - (img_to_draw.shape[0] // 2) - (depth // 2)
        overlay_transparent(img, img_to_draw, img_x, img_y)

    # 3. ADIM: Köşeleri Birleştir ve Ön Yüzü Çiz
    for f, b in zip(front_pts, back_pts):
        cv2.line(img, tuple(f), tuple(b), CIZGI_RENGI, 1)  # Derinlik çizgileri
    cv2.polylines(img, [front_pts], True, CIZGI_RENGI, 2)  # Ön yüz (Kalın)


# ==========================================
# 5. OYUN NESNELERİNİ BAŞLATMA
# ==========================================
kalibrasyon_noktalari = []
kalibrasyon_tamamlandi = False
matris = None  # Homography matrisi
puan = 0

hedef_objeler = []


def rastgele_varlik_sec():
    """ Havuzdan rastgele bir bayrak veya hayvan seçer """
    if varlik_havuzu:
        return random.choice(varlik_havuzu)
    return None


# Başlangıçta 5 tane rastgele obje oluştur
for _ in range(OBJE_SAYISI):
    hx = random.randint(100, OYUN_GENISLIK - 150)
    hy = random.randint(150, OYUN_YUKSEKLIK - 100)
    asset = rastgele_varlik_sec()
    hedef_objeler.append({'x': hx, 'y': hy, 'asset': asset})


def fare_tiklama(event, x, y, flags, param):
    """ Kalibrasyon için fare tıklamalarını kaydeder """
    global kalibrasyon_noktalari
    if event == cv2.EVENT_LBUTTONDOWN and not kalibrasyon_tamamlandi:
        kalibrasyon_noktalari.append((x, y))


# ==========================================
# 6. ANA PROGRAM DÖNGÜSÜ
# ==========================================
cap = cv2.VideoCapture(KAMERA_ID)

# Pencereleri oluştur
cv2.namedWindow("Goz (Telefon)")
cv2.setMouseCallback("Goz (Telefon)", fare_tiklama)
cv2.namedWindow("Oyun Alani", cv2.WINDOW_NORMAL)

global_frame_counter = 0  # Animasyon zamanlaması için sayaç

while True:
    success, img = cap.read()
    if not success: break

    # Görüntüyü Ayna Moduna al (Kullanım kolaylığı için)
    img = cv2.flip(img, 1)
    global_frame_counter += 1

    # --- MOD 1: KALİBRASYON ---
    if not kalibrasyon_tamamlandi:
        cv2.putText(img, f"Kalibrasyon: {len(kalibrasyon_noktalari)}/4", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255), 2)
        # Seçilen noktaları ekranda göster
        for pt in kalibrasyon_noktalari:
            cv2.circle(img, pt, 5, (0, 255, 0), -1)

        # 4 Nokta seçildiyse Perspektif Dönüşüm Matrisini Hesapla
        if len(kalibrasyon_noktalari) == 4:
            src_pts = np.float32(kalibrasyon_noktalari)  # Kaynak (Kamera)
            dst_pts = np.float32([[0, 0], [OYUN_GENISLIK, 0], [OYUN_GENISLIK, OYUN_YUKSEKLIK],
                                  [0, OYUN_YUKSEKLIK]])  # Hedef (Oyun Ekranı)
            matris = cv2.getPerspectiveTransform(src_pts, dst_pts)
            kalibrasyon_tamamlandi = True
            print("Kalibrasyon Tamamlandı! Oyun Başlıyor...")

    # --- MOD 2: OYUN ---
    else:
        # Beyaz Arka Plan Oluştur
        oyun_ekrani = np.zeros((OYUN_YUKSEKLIK, OYUN_GENISLIK, 3), dtype=np.uint8)
        oyun_ekrani[:] = ARKA_PLAN_RENGI

        # El Tespiti Başlat
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        detected_pos = None

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # İşaret parmağının ucunu al (Landmark ID: 8)
                index_finger = hand_lms.landmark[8]
                h, w, c = img.shape
                # Normalize edilmiş koordinatları piksele çevir
                cx, cy = int(index_finger.x * w), int(index_finger.y * h)

                # --- KOORDİNAT DÖNÜŞÜMÜ (MAPPING) ---
                # Kameradaki parmak konumunu, Homography matrisi ile Oyun Ekranı koordinatına çevir
                pts = np.array([[[cx, cy]]], dtype='float32')
                warped_pt = cv2.perspectiveTransform(pts, matris)[0][0]
                detected_pos = (int(warped_pt[0]), int(warped_pt[1]))

                # Oyun alanında imleci (Kırmızı Nokta) çiz
                cv2.circle(oyun_ekrani, detected_pos, 15, (0, 0, 255), -1)

        # --- NESNELERİ ÇİZ VE KONTROL ET ---
        for obje in hedef_objeler:
            # 3D Kutuyu ve içindeki varlığı (animasyon/resim) çiz
            draw_3d_content_box(oyun_ekrani, (obje['x'], obje['y']), KUP_BOYUTU, obje['asset'], global_frame_counter)

            # Çarpışma Kontrolü (Collision Detection)
            if detected_pos:
                # Eğer parmak küpün içindeyse (basit mesafe kontrolü)
                if abs(detected_pos[0] - obje['x']) < KUP_BOYUTU / 2 + 20 and abs(
                        detected_pos[1] - obje['y']) < KUP_BOYUTU / 2 + 20:
                    puan += 1
                    # Objeyi yeni rastgele bir konuma taşı
                    obje['x'] = random.randint(100, OYUN_GENISLIK - 150)
                    obje['y'] = random.randint(150, OYUN_YUKSEKLIK - 100)
                    # Vurulan obje şekil değiştirsin (Sürpriz olsun)
                    obje['asset'] = rastgele_varlik_sec()

        # Puan Durumunu Yaz
        cv2.putText(oyun_ekrani, f"Puan: {puan}", (30, 60), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
        cv2.imshow("Oyun Alani", oyun_ekrani)

    # Kamera Görüntüsünü Göster
    cv2.imshow("Goz (Telefon)", img)

    # 'q' tuşuna basılırsa çık
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()