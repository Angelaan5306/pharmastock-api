import asyncio
import os
from typing import List, Optional

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from database import DB_PATH
from models import (
    TransactionCreate,
    TransactionCreateResponse,
    TransactionResponse,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# asyncio.Lock melindungi critical section pada satu proses worker.
# Mode demo tanpa lock hanya untuk membuktikan race condition sesuai instruksi UTS.
stok_lock = asyncio.Lock()
DEMO_NO_LOCK = os.getenv("DEMO_NO_LOCK", "0") == "1"

async def _reserve_stock(medicine_id: int, jumlah: int):
    """
    Membaca stok, memberi jeda kecil, lalu menguranginya.
    Dalam mode normal seluruh critical section dilindungi oleh asyncio.Lock.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA busy_timeout = 5000")

        async with db.execute(
            "SELECT id, nama_obat, harga, stok FROM medicines WHERE id = ?",
            (medicine_id,),
        ) as cursor:
            medicine = await cursor.fetchone()

        if medicine is None:
            raise HTTPException(status_code=404, detail="Obat tidak ditemukan")

        if medicine["stok"] < jumlah:
            raise HTTPException(status_code=409, detail="Stok obat tidak mencukupi")

        # Jeda ini sengaja disediakan untuk membuka peluang race condition
        # saat pengujian dua request secara bersamaan.
        await asyncio.sleep(0.01)

        # UPDATE aritmetika membuat dua request tanpa lock dapat mengurangi
        # stok yang sama dua kali, sehingga overselling dapat diamati.
        await db.execute(
            "UPDATE medicines SET stok = stok - ? WHERE id = ?",
            (jumlah, medicine_id),
        )

        total = float(medicine["harga"]) * jumlah
        cursor = await db.execute(
            """
            INSERT INTO transactions
                (medicine_id, nama_obat, jumlah, harga_satuan, total_harga, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (medicine_id, medicine["nama_obat"], jumlah, medicine["harga"], total),
        )
        await db.commit()

        return {
            "id": cursor.lastrowid,
            "medicine_id": medicine_id,
            "nama_obat": medicine["nama_obat"],
            "jumlah": jumlah,
            "total_harga": total,
        }

async def proses_transaksi_background(trx_id: int):
    """Worker internal: pending -> processing -> completed."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE transactions SET status = 'processing' WHERE id = ?",
                (trx_id,),
            )
            await db.commit()

        # Simulasi pekerjaan I/O asynchronous sesuai ketentuan UTS.
        await asyncio.sleep(3)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE transactions SET status = 'completed' WHERE id = ?",
                (trx_id,),
            )
            await db.commit()

    except Exception:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE transactions SET status = 'failed' WHERE id = ?",
                (trx_id,),
            )
            await db.commit()

@router.post(
    "",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_transaction(data: TransactionCreate, bg: BackgroundTasks):
    """
    Membuat transaksi dan segera mengembalikan status pending.
    Pengurangan stok dilakukan sebelum response agar stok langsung terreservasi.
    """
    if DEMO_NO_LOCK:
        # HANYA untuk Tahap 1 pengujian UTS. Jangan gunakan untuk operasi normal.
        result = await _reserve_stock(data.medicine_id, data.jumlah)
    else:
        # Critical section: cek stok dan pengurangan stok dilakukan bergantian.
        async with stok_lock:
            result = await _reserve_stock(data.medicine_id, data.jumlah)

    bg.add_task(proses_transaksi_background, result["id"])

    return {
        **result,
        "status": "pending",
        "message": "Transaksi diterima dan sedang diproses di latar belakang",
    }

@router.get("", response_model=List[TransactionResponse])
async def get_all_transactions(
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    """Melihat transaksi; dapat difilter dengan ?status=pending."""
    allowed = {"pending", "processing", "completed", "failed"}
    if status_filter is not None and status_filter not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Status harus salah satu dari: {', '.join(sorted(allowed))}",
        )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status_filter:
            query = "SELECT * FROM transactions WHERE status = ? ORDER BY id DESC"
            params = (status_filter,)
        else:
            query = "SELECT * FROM transactions ORDER BY id DESC"
            params = ()

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

@router.get("/{trx_id}", response_model=TransactionResponse)
async def get_transaction_detail(trx_id: int):
    """Memantau status terkini satu transaksi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM transactions WHERE id = ?", (trx_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
            return dict(row)