# Sistem Pemantauan dan Pengendalian PLTS IoT Puskesmas

Sistem monitoring dan pengendalian Pembangkit Listrik Tenaga Surya (PLTS) berbasis Internet of Things (IoT) yang diimplementasikan di Puskesmas Tana Toraja. Proyek ini merupakan implementasi tugas akhir untuk memastikan ketersediaan listrik yang stabil dan efisien dalam mendukung operasional pelayanan kesehatan di Puskesmas.

## 🌟 Fitur Sistem

Sistem ini menyediakan kemampuan pemantauan dan pengendalian PLTS secara real-time:

- Monitoring parameter sistem PLTS:
  - Tegangan dan arus panel surya
  - Status pengisian dan kondisi baterai
  - Suhu komponen sistem
  - Efisiensi konversi energi

- Dashboard web untuk visualisasi dan kontrol:
  - Tampilan grafik real-time
  - Analisis performa sistem
  - Laporan penggunaan energi
  - Pengaturan parameter sistem

- Notifikasi otomatis untuk kondisi sistem:
  - Peringatan kondisi kritis
  - Alert penurunan performa
  - Pengingat pemeliharaan rutin
  - Status konektivitas perangkat

## 🛠 Teknologi yang Digunakan

### Backend
- Python 3.10+ dengan FastAPI
- MongoDB untuk database
- MQTT untuk komunikasi IoT
- WebSocket untuk update real-time

### Frontend
- React 18
- Tailwind CSS
- Recharts untuk grafik
- WebSocket client

### Hardware IoT
- ESP32 dengan MicroPython
- Sensor tegangan dan arus
- Sensor suhu
- Modul WiFi

## 📦 Panduan Instalasi

### Kebutuhan Sistem
- Python 3.10 atau lebih baru
- Node.js 18+
- MongoDB
- ESP32 dengan MicroPython

### Instalasi Backend

```bash
# Clone repository
git clone https://github.com/khalifardy/plts-iot-puskesmas.git
cd plts-iot-puskesmas

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install poetry
poetry install

# Setup environment variables
cp .env.example .env
# Edit .env sesuai konfigurasi

# Jalankan server
uvicorn app.main:app --reload
```

### Instalasi Frontend

```bash
# Masuk ke direktori frontend
cd frontend

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

### Setup IoT Device

1. Flash MicroPython ke ESP32
2. Upload kode firmware:
```bash
cd firmware
ampy --port /dev/ttyUSB0 put main.py
```

## 📊 Panduan Penggunaan dan Pemeliharaan

### Penggunaan Sistem
1. Akses dashboard web di `http://localhost:3000`
2. Login dengan kredensial administrator
3. Monitor kondisi sistem melalui dashboard
4. Atur parameter sistem sesuai kebutuhan
5. Unduh laporan performa secara berkala

### Pemeliharaan Rutin
1. Kalibrasi sensor setiap 6 bulan
2. Update firmware ketika tersedia
3. Backup database setiap minggu
4. Periksa kondisi fisik perangkat setiap bulan

## 📍 Lokasi Implementasi

Puskesmas Tana Toraja  
Jl. Poros Rantepao - Makale, Tambunan  
Kec. Makale Utara, Kabupaten Tana Toraja  
Sulawesi Selatan

## 📝 Dokumentasi

Dokumentasi lengkap tersedia di folder `/docs`, mencakup:
- Panduan teknis sistem
- Manual penggunaan
- Prosedur pemeliharaan
- Troubleshooting guide

---

Dikembangkan sebagai bagian dari Tugas Akhir Program Studi Sarjana S1 Informatika PJJ, Fakultas Informatika, Universitas Telkom.
