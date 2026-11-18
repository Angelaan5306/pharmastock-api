import asyncio
import aiosqlite

from database import DB_PATH, init_db

INITIAL_MEDICINES = [
    ("Paracetamol 500mg", "Obat Bebas", 5000.0, 50, "Strip", "Obat pereda nyeri dan demam"),
    ("Amoxicillin 500mg", "Antibiotik", 12000.0, 30, "Strip", "Antibiotik; penggunaan sesuai resep tenaga medis"),
    ("Ibuprofen 400mg", "Obat Bebas Terbatas", 8500.0, 40, "Strip", "Obat antiinflamasi"),
    ("Antasida Doen", "Obat Bebas", 4000.0, 60, "Botol", "Obat untuk membantu meredakan gejala asam lambung"),
    ("Vitamin C 1000mg", "Suplemen", 25000.0, 25, "Botol", "Suplemen vitamin C"),
    ("Cetirizine 10mg", "Antihistamin", 6000.0, 35, "Strip", "Antihistamin"),
    ("Omeprazole 20mg", "Obat Keras", 15000.0, 20, "Strip", "Penghambat produksi asam lambung; sesuai resep"),
    ("Salep Kulit 88", "Obat Topikal", 9000.0, 15, "Pcs", "Produk topikal"),
    ("Betadine 15ml", "Antiseptik", 18000.0, 50, "Botol", "Antiseptik luar"),
    ("OBH Combi Batuk", "Obat Batuk", 16000.0, 25, "Botol", "Obat batuk"),
]

async def seed_data():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        # Seed memakai INSERT OR IGNORE agar dapat dijalankan berulang
        # tanpa menghapus riwayat transaksi atau menggandakan data.
        await db.executemany(
            """
            INSERT INTO medicines
                (nama_obat, kategori, harga, stok, satuan, deskripsi)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM medicines WHERE nama_obat = ?
            )
            """,
            [row + (row[0],) for row in INITIAL_MEDICINES],
        )
        await db.commit()
    print("[OK] Data awal PharmaStock API siap (10 jenis obat).")

if __name__ == "__main__":
    asyncio.run(seed_data())