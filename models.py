from pydantic import BaseModel, Field, ConfigDict

class MedicineBase(BaseModel):
    nama_obat: str = Field(..., min_length=2, max_length=120, examples=["Paracetamol 500mg"])
    kategori: str = Field(..., min_length=2, max_length=60, examples=["Obat Bebas"])
    harga: float = Field(..., gt=0, examples=[5000.0])
    stok: int = Field(..., ge=0, examples=[50])
    satuan: str = Field(..., min_length=1, max_length=30, examples=["Strip"])
    deskripsi: str = Field(default="", max_length=300, examples=["Obat pereda nyeri dan demam"])

class MedicineCreate(MedicineBase):
    pass

class MedicineUpdate(MedicineBase):
    pass

class MedicineResponse(MedicineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class TransactionCreate(BaseModel):
    medicine_id: int = Field(..., gt=0, examples=[1])
    jumlah: int = Field(..., gt=0, examples=[2])

class TransactionCreateResponse(BaseModel):
    id: int
    medicine_id: int
    nama_obat: str
    jumlah: int
    total_harga: float
    status: str
    message: str

class TransactionResponse(BaseModel):
    id: int
    medicine_id: int
    nama_obat: str
    jumlah: int
    harga_satuan: float
    total_harga: float
    status: str
    created_at: str