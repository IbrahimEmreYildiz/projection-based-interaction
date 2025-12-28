import cv2  # Görüntü işleme
import numpy as np  # Matematiksel işlemler
import mediapipe as mp  # El takip sistemi
import random  # Rastgelelik (konum ve obje seçimi)
import os  # Dosya ve klasör yönetimi

# ==========================================
# 1. AYARLAR VE SABİTLER
# ==========================================
KAMERA_ID = 1  # Iriun Webcam genelde 1'dir. Görüntü yoksa 0 dene.
OYUN_GENISLIK = 1000
OYUN_YUKSEKLIK = 700
OBJE_SAYISI = 5  # Ekranda aynı anda kaç küp olacak
KUP_BOYUTU = 120  # Küplerin büyüklüğü

# Renk Tanımları (B, G, R)
RENK_BEYAZ = (255, 255, 255)
RENK_SIYAH = (0, 0, 0)
RENK_KIRMIZI = (50, 50, 255)  # Menü butonu için
RENK_YESIL = (50, 200, 50)  # Menü butonu için
RENK_MAVI = (255, 100, 50)  # Kalibrasyon noktaları

# Klasör Yolları
ANA_KLASOR = "3d_frames"
KLASOR_FLAGS = os.path.join(ANA_KLASOR, "flags")
KLASOR_ANIMALS = os.path.join(ANA_KLASOR, "animals")

# ==========================================
# 2. MEDIAPIPE KURULUMU
# ==========================================
mp_hands = mp.solutions.hands
# Güven oranı 0.7: El olduğundan emin olmadan algılama yapmaz (Titremeyi önler)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)


# ==========================================
# 3. GELİŞMİŞ VARLIK (ASSET) YÜKLEYİCİ
# ==========================================
def dosyalari_yukle():
    """
    Belirtilen klasörlerdeki resimleri tarar.
    Flags klasöründekileri 'Animasyon' gruplarına ayırır.
    Animals klasöründekileri 'Sabit Resim' olarak yükler.
    """
    assets_flags = []
    assets_animals = []

    print("--- YÜKLEME BAŞLADI ---")

    # --- 1. BAYRAKLARI YÜKLE (ANİMASYON MANTIĞI) ---
    if os.path.exists(KLASOR_FLAGS):
        dosyalar = sorted(os.listdir(KLASOR_FLAGS))
        gruplar = {}  # Örn: {'tr': [img1, img2], 'kr': [img1, img2]}

        for dosya in dosyalar:
            if not dosya.endswith(".png"): continue

            # Dosya ismini analiz et (Örn: k0.png -> Grup: 'k', index: 0)
            isim_kok = os.path.splitext(dosya)[0]  # Uzantıyı at

            # Grup adını bul (Sayıları atıp harfleri al)
            grup_adi = ''.join([i for i in isim_kok if not i.isdigit()])
            if grup_adi == "": grup_adi = "main"  # Eğer ismi sadece sayıysa (0.png) grubu 'main' yap

            path = os.path.join(KLASOR_FLAGS, dosya)
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # Şeffaf oku

            if img is not None:
                img = cv2.resize(img, (int(KUP_BOYUTU * 0.8), int(KUP_BOYUTU * 0.6)))

                if grup_adi not in gruplar:
                    gruplar[grup_adi] = []
                gruplar[grup_adi].append(img)

        # Gruplanmış resimleri listeye ekle
        for key, frames in gruplar.items():
            if len(frames) > 0:
                assets_flags.append({'type': 'anim', 'data': frames})
                print(f"Bayrak Grubu Yüklendi: '{key}' ({len(frames)} kare)")
    else:
        print(f"UYARI: '{KLASOR_FLAGS}' klasörü bulunamadı!")

    # --- 2. HAYVANLARI YÜKLE (SABİT RESİM MANTIĞI) ---
    if os.path.exists(KLASOR_ANIMALS):
        dosyalar = os.listdir(KLASOR_ANIMALS)
        for dosya in dosyalar:
            if not dosya.endswith(".png"): continue

            path = os.path.join(KLASOR_ANIMALS, dosya)
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

            if img is not None:
                # Hayvanları kareye yakın boyutlandır
                img = cv2.resize(img, (int(KUP_BOYUTU * 0.8), int(KUP_BOYUTU * 0.8)))
                assets_animals.append({'type': 'static', 'data': img})
                print(f"Hayvan Yüklendi: {dosya}")
    else:
        print(f"UYARI: '{KLASOR_ANIMALS}' klasörü bulunamadı!")

    return assets_flags, assets_animals


# Varlıkları hafızaya al
list_flags, list_animals = dosyalari_yukle()
aktif_liste = []  # O an seçili olan liste


# ==========================================
# 4. ÇİZİM VE GÖRSELLEŞTİRME FONKSİYONLARI
# ==========================================
def overlay_transparent(background, overlay, x, y):
    """ Şeffaf PNG resimlerini arka plana yapıştırır """
    bg_h, bg_w, _ = background.shape
    h, w, _ = overlay.shape

    # Ekran dışına taşmayı engelle
    if x + w > bg_w: w = bg_w - x
    if y + h > bg_h: h = bg_h - y
    if x < 0 or y < 0: return background

    overlay = overlay[:h, :w]

    # Alpha kanalı (Şeffaflık) kontrolü
    if overlay.shape[2] == 4:
        alpha = overlay[:, :, 3] / 255.0
        for c in range(3):
            background[y:y + h, x:x + w, c] = (alpha * overlay[:, :, c] +
                                               (1 - alpha) * background[y:y + h, x:x + w, c])
    else:
        background[y:y + h, x:x + w] = overlay


def draw_3d_box(img, center, size, asset_info, frame_counter):
    """
    3 Boyutlu Tel Kafes Küp çizer.
    İçine seçili olan varlığı (Animasyon veya Resim) yerleştirir.
    """
    cx, cy = center
    r = size // 2
    depth = size // 3  # Derinlik hissi

    # Köşe noktaları
    front_pts = np.array([[cx - r, cy - r], [cx + r, cy - r], [cx + r, cy + r], [cx - r, cy + r]], np.int32)
    back_pts = np.array([[cx - r + depth, cy - r - depth], [cx + r + depth, cy - r - depth],
                         [cx + r + depth, cy + r - depth], [cx - r + depth, cy + r - depth]], np.int32)

    # 1. Arka yüzü çiz (Siyah ince çizgi)
    cv2.polylines(img, [back_pts], True, RENK_SIYAH, 1)

    # 2. İçeriği yerleştir
    if asset_info:
        img_draw = None
        # Eğer sabit resimse (Hayvan)
        if asset_info['type'] == 'static':
            img_draw = asset_info['data']
        # Eğer animasyonsa (Bayrak)
        elif asset_info['type'] == 'anim':
            frames = asset_info['data']
            # Animasyon hızı (frame_counter'a göre döner)
            idx = (frame_counter // 4) % len(frames)
            img_draw = frames[idx]

        if img_draw is not None:
            # Resmi küpün ortasına hizala
            ix = cx - (img_draw.shape[1] // 2) + (depth // 2)
            iy = cy - (img_draw.shape[0] // 2) - (depth // 2)
            overlay_transparent(img, img_draw, ix, iy)

    # 3. Ön yüzü ve bağlantıları çiz
    for f, b in zip(front_pts, back_pts):
        cv2.line(img, tuple(f), tuple(b), RENK_SIYAH, 1)
    cv2.polylines(img, [front_pts], True, RENK_SIYAH, 2)


def menuyu_ciz(img):
    """ Oyun Başlangıç Ekranı (GUI) """
    h, w, _ = img.shape

    # Başlık
    cv2.putText(img, "PROJECTION INTERACTION", (w // 2 - 300, 150), cv2.FONT_HERSHEY_TRIPLEX, 1.5, RENK_SIYAH, 2)
    cv2.putText(img, "MOD SECINIZ", (w // 2 - 120, 220), cv2.FONT_HERSHEY_PLAIN, 2, RENK_SIYAH, 2)

    # Buton 1: BAYRAKLAR (Sol Taraf)
    # Kutu Çiz
    cv2.rectangle(img, (150, 350), (450, 550), RENK_KIRMIZI, 3)
    # Yazı Yaz
    cv2.putText(img, "BAYRAKLAR", (190, 460), cv2.FONT_HERSHEY_SIMPLEX, 1.2, RENK_KIRMIZI, 3)
    # İkon Göster (Varsa ilk bayrağı göster)
    if list_flags:
        ornek = list_flags[0]['data'][0]  # İlk animasyonun ilk karesi
        ornek = cv2.resize(ornek, (80, 60))
        overlay_transparent(img, ornek, 260, 370)

    # Buton 2: HAYVANLAR (Sağ Taraf)
    # Kutu Çiz
    cv2.rectangle(img, (550, 350), (850, 550), RENK_YESIL, 3)
    # Yazı Yaz
    cv2.putText(img, "HAYVANLAR", (590, 460), cv2.FONT_HERSHEY_SIMPLEX, 1.2, RENK_YESIL, 3)
    # İkon Göster
    if list_animals:
        ornek = list_animals[0]['data']
        ornek = cv2.resize(ornek, (80, 80))
        overlay_transparent(img, ornek, 660, 360)


# ==========================================
# 5. OYUN ALGORİTMASI VE DÖNGÜ
# ==========================================
cap = cv2.VideoCapture(KAMERA_ID)

# Oyun Durumları (State Machine)
STATE_KALIBRASYON = 0
STATE_MENU = 1
STATE_OYUN = 2
mevcut_durum = STATE_KALIBRASYON

# Değişkenler
kalibrasyon_noktalari = []
matris = None
puan = 0
hedef_objeler = []
global_frame_counter = 0


def fare_tiklama(event, x, y, flags, param):
    """ Kalibrasyon noktalarını seçmek için """
    if event == cv2.EVENT_LBUTTONDOWN and mevcut_durum == STATE_KALIBRASYON:
        kalibrasyon_noktalari.append((x, y))


# Pencereleri Oluştur
cv2.namedWindow("Goz (Telefon)")
cv2.setMouseCallback("Goz (Telefon)", fare_tiklama)
cv2.namedWindow("Oyun Alani", cv2.WINDOW_NORMAL)

print("Sistem Hazır. Kalibrasyon bekleniyor...")

while True:
    success, img = cap.read()
    if not success: break

    # Kamerayı Ayna Moduna al (Kullanım kolaylığı için)
    #img = cv2.flip(img, 1)
    global_frame_counter += 1

    # --- DURUM 0: KALİBRASYON ---
    if mevcut_durum == STATE_KALIBRASYON:
        cv2.putText(img, f"Kalibrasyon: {len(kalibrasyon_noktalari)}/4", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    RENK_MAVI, 2)
        for pt in kalibrasyon_noktalari:
            cv2.circle(img, pt, 5, (0, 255, 0), -1)

        # 4 Nokta seçilince matrisi hesapla ve Menüye geç
        if len(kalibrasyon_noktalari) == 4:
            src = np.float32(kalibrasyon_noktalari)
            dst = np.float32([[0, 0], [OYUN_GENISLIK, 0], [OYUN_GENISLIK, OYUN_YUKSEKLIK], [0, OYUN_YUKSEKLIK]])
            matris = cv2.getPerspectiveTransform(src, dst)
            mevcut_durum = STATE_MENU
            print("Kalibrasyon Tamam. Menü Açılıyor.")

    else:
        # Beyaz Arka Plan
        oyun_ekrani = np.zeros((OYUN_YUKSEKLIK, OYUN_GENISLIK, 3), dtype=np.uint8)
        oyun_ekrani[:] = RENK_BEYAZ

        # El Tespiti Yap
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        detected_pos = None

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # İşaret Parmağını Al
                index = hand_lms.landmark[8]
                h, w, c = img.shape
                cx, cy = int(index.x * w), int(index.y * h)

                # --- KOORDİNAT DÖNÜŞÜMÜ ---
                pts = np.array([[[cx, cy]]], dtype='float32')
                warped = cv2.perspectiveTransform(pts, matris)[0][0]
                detected_pos = (int(warped[0]), int(warped[1]))

                # Parmağın Yerine İmleç Çiz (Siyah Nokta)
                cv2.circle(oyun_ekrani, detected_pos, 15, RENK_SIYAH, -1)

        # --- DURUM 1: MENÜ EKRANI ---
        if mevcut_durum == STATE_MENU:
            menuyu_ciz(oyun_ekrani)

            if detected_pos:
                px, py = detected_pos

                # 1. Buton Kontrolü: BAYRAKLAR
                if 150 < px < 450 and 350 < py < 550:
                    if list_flags:
                        aktif_liste = list_flags
                        mevcut_durum = STATE_OYUN
                        puan = 0
                        # Yeni objeleri rastgele yerlere dağıt
                        hedef_objeler = []
                        for _ in range(OBJE_SAYISI):
                            hedef_objeler.append({
                                'x': random.randint(100, OYUN_GENISLIK - 150),
                                'y': random.randint(150, OYUN_YUKSEKLIK - 100),
                                'asset': random.choice(aktif_liste)
                            })
                    else:
                        print("Hata: Bayrak dosyaları bulunamadı!")

                # 2. Buton Kontrolü: HAYVANLAR
                elif 550 < px < 850 and 350 < py < 550:
                    if list_animals:
                        aktif_liste = list_animals
                        mevcut_durum = STATE_OYUN
                        puan = 0
                        hedef_objeler = []
                        for _ in range(OBJE_SAYISI):
                            hedef_objeler.append({
                                'x': random.randint(100, OYUN_GENISLIK - 150),
                                'y': random.randint(150, OYUN_YUKSEKLIK - 100),
                                'asset': random.choice(aktif_liste)
                            })
                    else:
                        print("Hata: Hayvan dosyaları bulunamadı!")

        # --- DURUM 2: OYUN EKRANI ---
        elif mevcut_durum == STATE_OYUN:
            # Geri Dönüş Bilgisi
            cv2.putText(oyun_ekrani, "MENU ICIN 'M' TUSUNA BASIN", (350, 680), cv2.FONT_HERSHEY_PLAIN, 1.2,
                        (100, 100, 100), 1)

            for obje in hedef_objeler:
                # 3D Küpü ve içindeki varlığı çiz
                draw_3d_box(oyun_ekrani, (obje['x'], obje['y']), KUP_BOYUTU, obje['asset'], global_frame_counter)

                # Çarpışma Kontrolü
                if detected_pos:
                    if abs(detected_pos[0] - obje['x']) < KUP_BOYUTU / 2 + 30 and abs(
                            detected_pos[1] - obje['y']) < KUP_BOYUTU / 2 + 30:
                        puan += 1
                        # Objeyi yeni yere ışınla
                        obje['x'] = random.randint(100, OYUN_GENISLIK - 150)
                        obje['y'] = random.randint(150, OYUN_YUKSEKLIK - 100)
                        # Yeni bir resim/animasyon seç
                        if aktif_liste:
                            obje['asset'] = random.choice(aktif_liste)

            # Puan Tablosu
            cv2.putText(oyun_ekrani, f"PUAN: {puan}", (30, 60), cv2.FONT_HERSHEY_PLAIN, 3, RENK_SIYAH, 3)

        cv2.imshow("Oyun Alani", oyun_ekrani)

    # Telefon görüntüsünü göster (Debug için)
    cv2.imshow("Goz (Telefon)", img)

    # Tuş kontrolleri
    tus = cv2.waitKey(1)
    if tus == ord('q'): break  # Çıkış
    if tus == ord('m'):  # Menüye Dön
        mevcut_durum = STATE_MENU
        print("Menüye dönüldü.")

cap.release()
cv2.destroyAllWindows()