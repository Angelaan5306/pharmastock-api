import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"
MEDICINE_ID = 6

async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        # Ambil data obat untuk mempertahankan field lainnya saat reset stok.
        response = await client.get(f"{BASE_URL}/medicines/{MEDICINE_ID}")
        response.raise_for_status()
        medicine = response.json()
        medicine["stok"] = 1

        reset = await client.put(f"{BASE_URL}/medicines/{MEDICINE_ID}", json=medicine)
        reset.raise_for_status()
        print(f"[RESET] Stok {medicine['nama_obat']} diatur menjadi 1.")

        payload = {"medicine_id": MEDICINE_ID, "jumlah": 1}
        print("[MULAI] Mengirim dua request transaksi secara bersamaan...")

        response_1, response_2 = await asyncio.gather(
            client.post(f"{BASE_URL}/transactions", json=payload),
            client.post(f"{BASE_URL}/transactions", json=payload),
        )

        print("\n--- HASIL PENGUJIAN RACE CONDITION ---")
        print("Request 1:", response_1.status_code, response_1.json())
        print("Request 2:", response_2.status_code, response_2.json())

        final_medicine = await client.get(f"{BASE_URL}/medicines/{MEDICINE_ID}")

        print("\n--- PEMERIKSAAN STOK AKHIR ---")
        print("HTTP Status:", final_medicine.status_code)
        print("Response:", repr(final_medicine.text))

        if final_medicine.status_code == 200:
            data = final_medicine.json()
            print("Stok akhir:", data.get("stok"))
        else:
            print("Gagal mengambil data obat.")

        print("\nEkspektasi:")
        print("- Tanpa lock: dua request dapat diterima dan stok dapat menjadi -1.")
        print("- Dengan lock: satu request diterima, satu ditolak HTTP 409, stok 0.")

if __name__ == "__main__":
    asyncio.run(main())