# Laprakin — Generator Laporan Praktikum LabTIF UAD

Aplikasi web berbasis Flask untuk membuat laporan praktikum (`.docx`) secara otomatis dan terstruktur sesuai format Laboratorium Teknik Informatika (LabTIF) Universitas Ahmad Dahlan, lengkap dengan integrasi **Google Gemini API** untuk menghasilkan isi teknis laporan secara multimodal.

---

## Fitur Utama

- **Autentikasi Pengguna**: Registrasi, login, dan reset password (`/signup`, `/login`, `/forgot-password`) dengan penyimpanan SQLite (`laprakin.db`).
- **4 Modul Praktikum Terintegrasi**:
  - **Komunikasi Data & Jaringan Komputer (`kdjk`)** — 14 pertemuan (*Cisco Packet Tracer & Winbox*)
  - **Struktur Data (`sdata`)** — 11 pertemuan (*C++*)
  - **Basis Data (`basdat`)** — 12 pertemuan (*MySQL, ERD & MongoDB*)
  - **Statistika Informatika (`statistika`)** — 14 pertemuan (*SPSS, MS Excel & Python*)
- **Generasi Konten AI Multimodal (`gemini_service.py`)**:
  - Menghasilkan daftar *Alat dan Bahan*, *Langkah Kerja*, keterangan teknis gambar (gambar Pre Test, Hasil Praktikum, dan Post Test), *Analisis Hasil*, serta *Ulasan Praktikum* dari prompt dan gambar tangkapan layar.
- **Generator Dokumen `.docx` Otomatis (`docx_generator.py`)**:
  - Sampul resmi berlogo UAD, format bab (`I. Pre Test`, `II. Hasil Praktikum`, `III. Post Test`, dan `Ulasan Praktikum`).
  - Penomoran gambar & kode program otomatis per bab (`Gambar 1.x`, `Gambar 2.x`, `Kode Program 2.x`, dst.) beserta prefix `Ket : ` pada setiap keterangan gambar.
  - Auto-italic untuk istilah teknis/bahasa asing dan kompresi gambar otomatis via Pillow.
  - Penamaan file `.docx` otomatis sesuai aturan masing-masing modul.
- **Riwayat Laporan**: Daftar dan unduh ulang laporan yang pernah dibuat (`/api/reports`).
- **Admin Panel (`/admin`)**: Dashboard statistik pengguna, distribusi modul, dan laporan terbaru yang dilindungi PIN 4 digit.

---

## Struktur Proyek

```text
laprak-generator/
├── app.py                  # Aplikasi utama Flask & endpoint API
├── db.py                   # Koneksi dan inisialisasi schema SQLite
├── docx_generator.py       # Builder dokumen .docx & metadata modul
├── gemini_service.py       # Integrasi multimodal Google Gemini API
├── requirements.txt        # Dependensi Python
├── static/                 # Aset CSS, JS (wizard.js), dan logo UAD
└── templates/              # Template HTML (wizard, auth, admin, legal)
```

---

## Persyaratan

- Python 3.10+ (diuji pada Python 3.12)
- `GEMINI_API_KEY` dari Google AI Studio

---

## Cara Menjalankan

### 1. Linux / macOS

```bash
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r requirements.txt
```

Set environment variable `GEMINI_API_KEY` (atau simpan di file `.env`):

```bash
export GEMINI_API_KEY="api_key_gemini_anda"
```

Jalankan server:

```bash
python app.py
```

### 2. Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set GEMINI_API_KEY=api_key_gemini_anda
python app.py
```

Aplikasi akan berjalan di **`http://127.0.0.1:5000`**.

---

## Konfigurasi Environment Variable

| Variabel | Keterangan | Default |
|---|---|---|
| `GEMINI_API_KEY` | API Key Google Gemini (bisa juga diletakkan di file `.env`) | *(wajib untuk fitur AI)* |
| `LAPRAKIN_ADMIN_PIN` | PIN 4 digit untuk membuka halaman `/admin` | `2026` |
| `LAPRAKIN_SECRET_KEY` | Secret key Flask session | `laprakin-labtif-uad-2026-secret` |
