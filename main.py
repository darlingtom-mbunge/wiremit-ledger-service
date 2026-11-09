import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Wiremit Remittance Ledger Service",
    description="Microservice demonstrating atomic wallet transfers, fee calculations, and idempotency protection.",
    version="1.0.0"
)

def get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            account_id TEXT PRIMARY KEY,
            currency TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT,
            amount REAL,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO wallets VALUES ('ACC-USD-001', 'USD', 5000.00)")
    cursor.execute("INSERT OR IGNORE INTO wallets VALUES ('ACC-ZAR-002', 'ZAR', 1000.00)")
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()

class TransferRequest(BaseModel):
    sender_id: str = Field(..., example="ACC-USD-001")
    recipient_id: str = Field(..., example="ACC-ZAR-002")
    amount: float = Field(..., gt=0, example=150.00)
    currency: str = Field(..., example="USD")

@app.get("/")
def root():
    return {"status": "healthy", "service": "Wiremit Remittance Ledger API", "docs": "/docs"}

@app.get("/api/v1/wallets/{account_id}")
def get_wallet(account_id: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM wallets WHERE account_id = ?", (account_id,))
    wallet = cursor.fetchone()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet account not found")
    return dict(wallet)

@app.post("/api/v1/transactions/transfer", status_code=status.HTTP_201_CREATED)
def execute_transfer(
    payload: TransferRequest, 
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: sqlite3.Connection = Depends(get_db)
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="X-Idempotency-Key header is required for financial safety")

    cursor = db.cursor()

    cursor.execute("SELECT * FROM ledger WHERE transaction_id = ?", (idempotency_key,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Duplicate transaction detected (Idempotency Key reused)")

    cursor.execute("SELECT balance FROM wallets WHERE account_id = ?", (payload.sender_id,))
    sender = cursor.fetchone()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found")
    
    fee = round(payload.amount * 0.015, 2)
    total_deduction = payload.amount + fee

    if sender["balance"] < total_deduction:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Required: {total_deduction}, Available: {sender['balance']}")

    new_sender_balance = sender["balance"] - total_deduction
    cursor.execute("UPDATE wallets SET balance = ? WHERE account_id = ?", (new_sender_balance, payload.sender_id))
    cursor.execute("INSERT INTO ledger VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", 
                   (idempotency_key, payload.sender_id, -total_deduction, "TRANSFER_OUT"))
    db.commit()

    return {
        "status": "SUCCESS",
        "transaction_id": idempotency_key,
        "amount_transferred": payload.amount,
        "fee_charged": fee,
        "new_sender_balance": new_sender_balance
    }
