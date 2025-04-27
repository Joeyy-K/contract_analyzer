# Contract Analyzer API

A powerful API for analyzing legal contracts built with FastAPI. The system allows users to upload PDF and DOCX contracts, extract their content, and analyze key clauses using modern NLP techniques.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.1-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🌟 Features

- **Document Processing**: Upload and parse PDF and DOCX contracts
- **Contract Analysis**: Extract key clauses including:
  - Termination clauses
  - Confidentiality provisions
  - Payment terms
  - Governing law
  - Limitation of liability
- **User Authentication**: Secure JWT-based authentication system
- **RESTful API**: Modern API design with comprehensive documentation
- **AI-Powered**: Integration with Hugging Face inference API for intelligent clause extraction

## 📋 Requirements

- Python 3.9+
- FastAPI
- SQLAlchemy
- PyMuPDF (for PDF parsing)
- python-docx (for DOCX parsing)
- Pydantic
- Python-Jose (JWT tokens)
- Passlib (password hashing)
- Uvicorn (ASGI server)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Joeyy-K/contract_analyzer.git
cd contract-analyzer-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```
DATABASE_URL=sqlite:///./contract_analyzer.db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HUGGINGFACE_API_TOKEN=your_huggingface_token
```

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to see the API documentation.

## 🔌 API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Contracts

- `POST /api/v1/contracts/upload` - Upload a contract file (PDF/DOCX)
- `GET /api/v1/contracts/` - List all user contracts
- `GET /api/v1/contracts/{contract_id}` - Get contract details
- `POST /api/v1/contracts/{contract_id}/analyze` - Analyze contract clauses

## 📊 Data Models

### User

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2023-04-20T12:00:00"
}
```

### Contract

```json
{
  "id": 1,
  "filename": "contract.pdf",
  "file_type": "pdf",
  "uploaded_at": "2023-04-20T14:30:00"
}
```

### Contract Analysis

```json
{
  "contract_id": 1,
  "analysis": {
    "termination_clause": "This Agreement may be terminated by either party with 30 days written notice...",
    "confidentiality_clause": "All information shared between parties shall be kept confidential...",
    "payment_terms": "Payment shall be made within 30 days of invoice...",
    "governing_law": "This Agreement shall be governed by the laws of California...",
    "limitation_of_liability": "In no event shall either party be liable for indirect damages..."
  }
}
```

## 🛠️ Project Structure

```
contract-analyzer-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── contracts.py
│   │       └── auth.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── crud/
│   │   ├── contract.py
│   │   └── user.py
│   ├── db/
│   │   ├── base.py
│   │   ├── base_class.py
│   │   └── session.py
│   ├── models/
│   │   ├── contract.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── analysis.py
│   │   ├── contract.py
│   │   └── user.py
│   ├── services/
│   │   ├── contract_analyzer.py
│   │   ├── docx_parser.py
│   │   ├── file_parser.py
│   │   └── pdf_parser.py
│   └── main.py
├── requirements.txt
└── README.md
```

## 📝 Usage Examples

### 1. Create a new user

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password123", "full_name": "John Doe"}'
```

### 2. Login and get access token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=password123"
```

### 3. Upload a contract

```bash
curl -X POST "http://localhost:8000/api/v1/contracts/upload" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "file=@/path/to/your/contract.pdf"
```

### 4. Analyze a contract

```bash
curl -X POST "http://localhost:8000/api/v1/contracts/1/analyze" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```


## 🚧 Roadmap

- [ ] Add support for more document formats
- [ ] Implement batch processing of multiple contracts
- [ ] Add contract comparison feature
- [ ] Create a web frontend
- [ ] Implement advanced NLP features using custom models

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Hugging Face](https://huggingface.co/) for NLP models and inference API
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- [python-docx](https://python-docx.readthedocs.io/) for DOCX processing