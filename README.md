# Wiremit Multi-Currency Ledger Microservice

A production-ready RESTful backend API built with **FastAPI** to handle core remittance ledger operations, atomic wallet updates, and financial idempotency checks.

## 🚀 Key Architectural Features

- **Idempotency Protection**: Rejects duplicate execution of financial requests using the `X-Idempotency-Key` header to protect against double-spending caused by network retries.
- **Transactional Balance Deduction**: Real-time balance integrity check with automated processing fee calculations (1.5%).
- **Interactive OpenAPI Documentation**: Built-in interactive Swagger UI generated automatically at `/docs`.
- **Data Integrity**: Uses Pydantic data schemas to enforce structural validation on incoming payloads.

## 🛠️ Tech Stack
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn ASGI
- **Database**: SQLite (In-Memory Transactional Store)

## 📋 Key API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check & API metadata |
| `GET` | `/api/v1/wallets/{account_id}` | Query wallet balances |
| `POST` | `/api/v1/transactions/transfer` | Execute atomic monetary transfer |

## ⚙️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/darlingtom-mbunge/wiremit-ledger-service.git](https://github.com/darlingtom-mbunge/wiremit-ledger-service.git)
   cd wiremit-ledger-service
