import cv2
import numpy as np
import mediapipe as mp
import random

# --- AYARLAR ---
# Telefonunu bağlayınca genelde 0, 1 veya 2 olur.
# Eğer görüntü gelmezse bu sayıyı değiştir.
KAMERA_ID = 0

# Sanal Oyun Alanı (Laptop Ekranı)
OYUN_GENISLIK = 1000
OYUN_YUKSEKLIK = 700

# --- MEDIAPIPE (İskelet Takibi) ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# --- DEĞİŞKENLER ---
kalibrasyon_noktalari = []
kalibrasyon_tamamlandi = False
matris = None

# Hedef Obje (3D Küp) Konumu
hedef_x, hedef_y = 500, 350
puan = 0


def fare_tiklama(event, x, y, flags, param):
    """ Kalibrasyon için 4 köşe seçimi """
    global kalibrasyon_noktalari
    if event == cv2.EVENT_LBUTTONDOWN and not kalibrasyon_tamamlandi:
        kalibrasyon_noktalari.append((x, y))
        print(f"Nokta {len(kalibrasyon_noktalari)} Secildi: {x}, {y}")


def draw_3d_cube(img, center, size, color=(0, 255, 255)):
    """ Basit 3D Küp Çizimi """
    cx, cy = center
    r = size // 2
    depth = size // 3

    # Ön Yüz
    front = np.array([[cx - r, cy - r], [cx + r, cy - r], [cx + r, cy + r], [cx - r, cy + r]], np.int32)
    # Arka Yüz
    back = np.array(
        [[cx - r + depth, cy - r - depth], [cx + r + depth, cy - r - depth], [cx + r + depth, cy + r - depth],
         [cx - r + depth, cy + r - depth]], np.int32)

    cv2.polylines(img, [front], True, color, 3)
    cv2.polylines(img, [back], True, color, 1)
    for f, b in zip(front, back):
        cv2.line(img, tuple(f), tuple(b), color, 1)


# --- ANA DÖNGÜ ---
cap = cv2.VideoCapture(KAMERA_ID)

cv2.namedWindow("Goz (Telefon)")
cv2.setMouseCallback("Goz (Telefon)", fare_tiklama)
cv2.namedWindow("Oyun Alani", cv2.WINDOW_NORMAL)

print("--- BASLIYORUZ ---")
print("1. Telefonu laptop ekranını görecek şekilde koy.")
print("2. 'Goz' penceresinde, ekrandaki 'Oyun Alani' penceresinin 4 KÖŞESİNE tıkla.")

while True:
    success, img = cap.read()
    if not success:
        print("Kamera acilmadi! KAMERA_ID'yi degistir.")
        break

    # 1. KALİBRASYON (Homography)
    if not kalibrasyon_tamamlandi:
        cv2.putText(img, f"Kalibrasyon: {len(kalibrasyon_noktalari)}/4", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255), 2)
        for pt in kalibrasyon_noktalari:
            cv2.circle(img, pt, 5, (0, 255, 0), -1)

        if len(kalibrasyon_noktalari) == 4:
            src_pts = np.float32(kalibrasyon_noktalari)
            dst_pts = np.float32([[0, 0], [OYUN_GENISLIK, 0], [OYUN_GENISLIK, OYUN_YUKSEKLIK], [0, OYUN_YUKSEKLIK]])
            matris = cv2.getPerspectiveTransform(src_pts, dst_pts)
            kalibrasyon_tamamlandi = True
            print("Kalibrasyon Tamam!")

    # 2. OYUN
    else:
        oyun_ekrani = np.zeros((OYUN_YUKSEKLIK, OYUN_GENISLIK, 3), dtype=np.uint8)

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)

        detected_pos = None

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
                index_finger = hand_lms.landmark[8]
                h, w, c = img.shape
                cx, cy = int(index_finger.x * w), int(index_finger.y * h)
                cv2.circle(img, (cx, cy), 10, (255, 0, 255), -1)

                # Koordinat Dönüşümü
                pts = np.array([[[cx, cy]]], dtype='float32')
                warped = cv2.perspectiveTransform(pts, matris)[0][0]
                detected_pos = (int(warped[0]), int(warped[1]))
                cv2.circle(oyun_ekrani, detected_pos, 20, (0, 0, 255), -1)

        # Oyun Mantığı
        draw_3d_cube(oyun_ekrani, (hedef_x, hedef_y), 80)
        if detected_pos:
            if abs(detected_pos[0] - hedef_x) < 50 and abs(detected_pos[1] - hedef_y) < 50:
                puan += 1
                hedef_x, hedef_y = random.randint(100, 900), random.randint(100, 600)

        cv2.putText(oyun_ekrani, f"Puan: {puan}", (30, 60), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
        cv2.imshow("Oyun Alani", oyun_ekrani)

    cv2.imshow("Goz (Telefon)", img)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()