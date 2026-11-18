from typing import List

import aiosqlite
from fastapi import APIRouter, HTTPException, Query, status

from database import DB_PATH
from models import MedicineCreate, MedicineUpdate, MedicineResponse

router = APIRouter(prefix="/medicines", tags=["Medicines"])

@router.get("", response_model=List[MedicineResponse])
async def get_all_medicines(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Menampilkan daftar obat dengan pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM medicines ORDER BY id LIMIT ? OFFSET ?",
            (limit, skip),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(data: MedicineCreate):
    """Menambahkan data obat baru."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO medicines
                (nama_obat, kategori, harga, stok, satuan, deskripsi)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.nama_obat, data.kategori, data.harga,
                data.stok, data.satuan, data.deskripsi,
            ),
        )
        await db.commit()
        new_id = cursor.lastrowid

        async with db.execute("SELECT * FROM medicines WHERE id = ?", (new_id,)) as cur:
            row = await cur.fetchone()
            columns = [item[0] for item in cur.description]
            return dict(zip(columns, row))

@router.get("/{med_id}", response_model=MedicineResponse)
async def get_medicine_detail(med_id: int):
    """Menampilkan detail satu obat."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM medicines WHERE id = ?", (med_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Obat tidak ditemukan")
            return dict(row)

@router.put("/{med_id}", response_model=MedicineResponse)
async def update_medicine(med_id: int, data: MedicineUpdate):
    """Memperbarui seluruh field obat berdasarkan ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM medicines WHERE id = ?", (med_id,)) as cursor:
            if await cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Obat tidak ditemukan")

        await db.execute(
            """
            UPDATE medicines
            SET nama_obat = ?, kategori = ?, harga = ?, stok = ?, satuan = ?, deskripsi = ?
            WHERE id = ?
            """,
            (
                data.nama_obat, data.kategori, data.harga,
                data.stok, data.satuan, data.deskripsi, med_id,
            ),
        )
        await db.commit()

        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM medicines WHERE id = ?", (med_id,)) as cursor:
            return dict(await cursor.fetchone())

@router.delete("/{med_id}", status_code=status.HTTP_200_OK)
async def delete_medicine(med_id: int):
    """Menghapus permanen obat; obat yang sudah memiliki transaksi tidak dihapus."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM medicines WHERE id = ?", (med_id,)) as cursor:
            if await cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Obat tidak ditemukan")

        async with db.execute(
            "SELECT id FROM transactions WHERE medicine_id = ? LIMIT 1", (med_id,)
        ) as cursor:
            if await cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Obat tidak dapat dihapus karena sudah memiliki riwayat transaksi",
                )

        await db.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
        await db.commit()
        return {"message": f"Obat dengan ID {med_id} berhasil dihapus permanen"}