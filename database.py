from pathlib import Path
import aiosqlite

# Lokasi database dibuat relatif terhadap folder proyek agar konsisten
# meskipun server dijalankan dari direktori kerja yang berbeda.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "apotek.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")

        # CHECK stok sengaja tidak dipasang agar mode demonstrasi tanpa lock
        # dapat memperlihatkan overselling (stok menjadi negatif).
        # Pada mode normal, validasi stok + asyncio.Lock mencegah kondisi ini.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_obat TEXT NOT NULL,
                kategori TEXT NOT NULL,
                harga REAL NOT NULL CHECK (harga > 0),
                stok INTEGER NOT NULL,
                satuan TEXT NOT NULL,
                deskripsi TEXT DEFAULT ''
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                nama_obat TEXT NOT NULL,
                jumlah INTEGER NOT NULL CHECK (jumlah > 0),
                harga_satuan REAL NOT NULL,
                total_harga REAL NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            )
        """)
        await db.commit()

async def get_db():
    """Dependency opsional untuk endpoint yang membutuhkan koneksi database."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")
        yield db