# PharmaStock API
Video presentasi: https://youtu.be/PvrlD-84gVs?si=ylWU3pCty4zyEUlD

REST API backend untuk manajemen obat dan transaksi penjualan apotek. Proyek ini dibuat untuk UTS Komputasi Paralel dan Terdistribusi dengan FastAPI, SQLite melalui `aiosqlite`, asynchronous processing, `BackgroundTasks`, dan `asyncio.Lock`.

> Proyek ini adalah simulasi akademik, bukan sistem operasional apotek. Data obat hanya data contoh. Sistem tidak memberikan rekomendasi atau keputusan penggunaan obat.

## 1. Fitur
- CRUD obat: tambah, daftar dengan pagination, detail, ubah, dan hapus permanen.
- Transaksi penjualan dengan status `pending`, `processing`, `completed`, atau `failed`.
- Pemrosesan transaksi menggunakan FastAPI `BackgroundTasks`.
- Operasi database asynchronous menggunakan `aiosqlite`.
- Pengamanan stok menggunakan `asyncio.Lock`.
- Mode demonstrasi race condition tanpa lock.
- Pengujian beban menggunakan Locust.

## 2. Struktur proyek
PharmaStock_API/
├── main.py
├── database.py
├── models.py
├── requirements.txt
├── README.md
├── seed.py
├── test_race.py
├── locustfile.py
├── apotek.db              # dibuat otomatis saat aplikasi dijalankan
├── routes/
│   ├── __init__.py
│   ├── resource.py
│   └── transaction.py
└── docs/
    └── laporan_uts.pdf    # draft laporan; lengkapi hasil pengujian aktual

## 3. Instalasi
Gunakan Python 3.10 atau lebih baru.

### Windows PowerShell
```powershell
cd PharmaStock_API
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

Jika PowerShell menolak aktivasi environment, jalankan:

```powershell
.venv\Scripts\activate.bat
```

Buka dokumentasi interaktif:

- Swagger UI: http://127.0.0.1:8000/docs
- Root API: http://127.0.0.1:8000/

Tidak diperlukan frontend terpisah. Seluruh endpoint dapat dicoba melalui Swagger UI.

## 4. Endpoint
| Method | Path | Keterangan |
|---|---|---|
| GET | `/medicines?skip=0&limit=10` | Daftar obat |
| GET | `/medicines/{med_id}` | Detail obat |
| POST | `/medicines` | Tambah obat |
| PUT | `/medicines/{med_id}` | Perbarui obat |
| DELETE | `/medicines/{med_id}` | Hapus permanen obat |
| POST | `/transactions` | Buat transaksi asynchronous |
| GET | `/transactions` | Daftar transaksi |
| GET | `/transactions?status=pending` | Filter transaksi berdasarkan status |
| GET | `/transactions/{trx_id}` | Detail dan status transaksi |

Kode status utama:
- `201 Created`: obat berhasil dibuat.
- `200 OK`: permintaan baca/perbarui/hapus berhasil.
- `202 Accepted`: transaksi diterima dan diproses di latar belakang.
- `404 Not Found`: ID obat/transaksi tidak ditemukan.
- `409 Conflict`: stok tidak cukup atau obat memiliki riwayat transaksi.
- `422 Unprocessable Entity`: validasi request gagal.

## 5. Contoh request
### Tambah obat
`POST /medicines`

```json
{
  "nama_obat": "Paracetamol 500mg",
  "kategori": "Obat Bebas",
  "harga": 5000,
  "stok": 50,
  "satuan": "Strip",
  "deskripsi": "Obat pereda nyeri dan demam"
}
```

### Buat transaksi
`POST /transactions`

```json
{
  "medicine_id": 1,
  "jumlah": 2
}
```

Response awal mengandung status `pending`. Cek `GET /transactions/{id}` setelah beberapa detik untuk melihat status berubah menjadi `completed`.

## 6. Pengujian race condition
Pengujian ini dilakukan pada satu worker agar demonstrasi `asyncio.Lock` sesuai dengan cakupan prosesnya.

### Tahap 1: tanpa lock
PowerShell:

```powershell
$env:DEMO_NO_LOCK="1"
uvicorn main:app --port 8000
```

Buka terminal kedua:

```powershell
python test_race.py
```

Dua request dapat membaca stok awal yang sama sebelum keduanya mengurangi stok. Hasil yang diharapkan pada mode demonstrasi adalah dua transaksi diterima dan stok akhir dapat menjadi `-1`.

### Tahap 2: dengan lock
Matikan server dengan `Ctrl+C`. Hapus variabel mode demo pada terminal PowerShell:

```powershell
Remove-Item Env:DEMO_NO_LOCK
uvicorn main:app --port 8000
```

Di terminal kedua:

```powershell
python test_race.py
```

Hasil yang diharapkan: satu request diterima (`202`), satu request ditolak (`409 Conflict`), dan stok akhir `0`.

**Penting:** `asyncio.Lock` adalah lock pada satu proses worker. Lock ini bukan lock lintas proses. Karena itu, demonstrasi race condition di atas menggunakan satu worker. Pada deployment multi-worker, perlindungan stok lintas proses memerlukan mekanisme atomik/transaksi database atau distributed lock. Jangan mengklaim `asyncio.Lock` saja melindungi seluruh worker.

## 7. Pengujian Locust
Jalankan server normal (tanpa mode demo), lalu di terminal lain:
```powershell
locust -f locustfile.py --host http://127.0.0.1:8000
```

Buka http://localhost:8089.

Lakukan skenario sesuai instruksi UTS:
- Read: 100 request, concurrency 20.
- Write: 50 request, concurrency 10.

Catat total waktu, throughput, dan rata-rata latensi. Ulangi dengan server 1 worker dan 4 worker. Gunakan data hasil pengujian aktual di laporan, jangan mengisi angka perkiraan.

## 8. Multi-worker
Matikan server sebelum mengganti jumlah worker.

```powershell
uvicorn main:app --workers 1 --port 8000
```

Kemudian:

```powershell
uvicorn main:app --workers 4 --port 8000
```

Jangan gunakan `--reload` bersamaan dengan `--workers`.

## 9. Catatan teknis
- Database dibuat otomatis saat aplikasi pertama kali dijalankan.
- Jalankan `python seed.py` untuk memasukkan 10 data awal. Seed tidak menghapus data dan riwayat transaksi.
- Penghapusan obat yang telah memiliki transaksi ditolak dengan `409` agar foreign key dan riwayat transaksi tetap konsisten.
- Mode `DEMO_NO_LOCK=1` hanya untuk demonstrasi race condition, bukan penggunaan normal.
- `BackgroundTasks` berjalan setelah response dikirim, tetapi bukan sistem antrean persisten. Untuk aplikasi produksi diperlukan worker/queue terpisah.
- `asyncio.Lock` hanya melindungi request dalam satu proses Python.