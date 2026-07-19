# RetailMind AI - Intelligent Retail Promotion Assistant

A modern AI-powered platform that helps grocery stores and supermarkets create, manage, and automate promotional offers using Artificial Intelligence.

## Features

- **AI Offer Generator** - Type "Rice 20% off till Sunday" and AI creates a complete promotional offer
- **OCR Smart Scanner** - Upload posters/flyers and AI extracts offers automatically
- **AI Voice Announcements** - Convert announcements to speech with scheduled playback
- **Multilingual Support** - Generate announcements in English, Hindi, and Bengali
- **AI Chatbot** - Ask questions about stock, offers, and get AI-powered recommendations
- **Business Intelligence** - AI analyzes data and suggests promotions, discounts, and timing
- **Analytics Dashboard** - Charts, stats, and real-time store insights
- **Reports** - Daily/Weekly/Monthly reports with AI summaries, exportable to PDF/Excel
- **Background Music** - Mix voice announcements with royalty-free background music tracks
- **Professional UI** - Dark/Light mode, glassmorphism, responsive design

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, Tailwind CSS, Framer Motion, Chart.js |
| Backend | Python Flask, Flask-JWT-Extended, Flask-CORS |
| Database | SQLite + SQLAlchemy |
| AI | Google Gemini API (gemini-2.0-flash) |
| OCR | EasyOCR |
| TTS | gTTS (Google Text-to-Speech) |
| Audio | numpy + imageio-ffmpeg (mixing), pydub |
| Scheduler | APScheduler |
| Reports | ReportLab (PDF), openpyxl (Excel) |

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env file and add your Gemini API key
# GEMINI_API_KEY=your_key_here

# Run backend server
python app.py
```

The backend runs on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend runs on `http://localhost:5173`

## Default Login

- **Username:** admin
- **Password:** admin123

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | Login (returns JWT) |
| POST | /api/auth/logout | Logout |
| GET | /api/auth/me | Current user info |
| GET | /api/auth/logs | Activity logs |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/products | List products |
| POST | /api/products | Create product |
| PUT | /api/products/:id | Update product |
| DELETE | /api/products/:id | Delete product |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/categories | List categories |
| POST | /api/categories | Create category |
| PUT | /api/categories/:id | Update category |
| DELETE | /api/categories/:id | Delete category |

### Offers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/offers | List offers (filter: active/expired/all) |
| POST | /api/offers | Create offer |
| PUT | /api/offers/:id | Update offer |
| DELETE | /api/offers/:id | Delete offer |
| POST | /api/offers/:id/toggle | Toggle offer status |

### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/ai/generate-offer | Generate offer from natural language |
| POST | /api/ai/translate-announcement | Translate announcement |
| POST | /api/chat/message | Send chatbot message |
| GET | /api/chat/history | Get chat history |
| POST | /api/chat/clear | Clear chat history |
| GET | /api/intelligence/recommendations | Get AI recommendations |
| POST | /api/ocr/scan | Scan image for offers |

### TTS, Announcements & Music
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/tts/generate | Generate speech from text |
| POST | /api/tts/announce/:id | Play announcement now |
| POST | /api/tts/schedule/:id | Schedule announcement |
| POST | /api/tts/stop/:id | Stop scheduled announcement |
| GET | /api/tts/list | List all announcements |
| GET | /api/tts/music-tracks | List background music tracks |
| POST | /api/tts/preview | Preview voice + music mix |
| POST | /api/tts/mix/:id | Mix announcement with music |
| GET | /api/tts/download/:id | Download announcement MP3 |

### Reports & Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/dashboard/stats | Dashboard statistics |
| GET | /api/reports/daily | Daily report |
| GET | /api/reports/weekly | Weekly report |
| GET | /api/reports/monthly | Monthly report |
| GET | /api/reports/:period/export/pdf | Export as PDF |
| GET | /api/reports/:period/export/excel | Export as Excel |

## Database Schema

```
Users          Products         Categories       Offers
- id           - id             - id             - id
- username     - name           - name           - product_id
- password     - brand          - description    - title
- role         - category_id                     - description
- created_at   - price                           - announcement_text
               - discount                        - discount_percent
               - final_price                     - start_date
               - stock_quantity                   - end_date
               - image_url                        - is_active
               - created_at                       - language

Announcements  ActivityLogs     ChatMessages
- id           - id             - id
- offer_id     - user_id        - user_id
- audio_file   - action         - role
- language     - details        - content
- bg_music     - timestamp      - timestamp
- music_vol
- interval
- last_played
- is_active
```

## Configuration

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///database/retailmind.db
FLASK_ENV=development
SECRET_KEY=your-flask-secret
```

## Project Structure

```
retailmind-ai/
├── backend/
│   ├── ai/              # AI modules (Gemini, chatbot, intelligence)
│   ├── assets/music/    # Background music tracks (4 royalty-free)
│   ├── audio/           # Generated & mixed audio files
│   ├── database/        # DB initialization & seeding
│   ├── models/          # SQLAlchemy models
│   ├── ocr/             # OCR scanner (EasyOCR)
│   ├── routes/          # API endpoints
│   ├── scripts/         # Music track generator
│   ├── services/        # Scheduler & audio mixer
│   ├── tts/             # Text-to-Speech engine (gTTS)
│   ├── uploads/         # Uploaded images
│   ├── utils/           # Helpers & decorators
│   ├── app.py           # Main Flask application
│   ├── config.py        # Configuration
│   ├── requirements.txt # Python dependencies
│   └── .env             # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   ├── context/     # React context (Auth, Theme)
│   │   ├── services/    # API service (Axios)
│   │   ├── hooks/       # Custom hooks
│   │   ├── App.jsx      # Main app with routing
│   │   └── main.jsx     # Entry point
│   ├── package.json     # Node.js dependencies
│   └── vite.config.js   # Vite configuration
├── requirements.txt     # Python dependencies (root copy)
└── README.md
```

## License

MIT
