
# AuraPlan - Lightweight Personal Productivity Assistant

AuraPlan is an **AI-powered productivity assistant** that transforms natural language input into structured tasks, notes, and reminders.  
It runs **entirely offline** using a **local LLM**, ensuring complete data privacy.

---

## Features

- ** Natural Language Input** - Type tasks like you text a friend: *"Buy milk tomorrow"* → auto-parsed and organized
- ** Local LLM Processing** - Uses Ollama (Llama 3.2) running locally—zero cloud, complete privacy
- ** Semantic Search** - Find tasks by meaning, not keywords (powered by ChromaDB)
- ** Smart Organization** - Auto-categorizes as tasks/notes/reminders, assigns priority & tags
- ** Lightweight** - Minimal dependencies, optimized for local execution
- ** Clean UI** - Distraction-free dashboard with filtering, sorting, and visual day view
- ** Calendar/Email Sync** - Framework ready for Google Calendar & Gmail integration (mock data available)
- ** Task Management** - Create, read, update, delete, complete, search operations

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite | Fast, modern UI |
| **Backend** | Flask + SQLite | Lightweight API & storage |
| **AI/LLM** | Ollama (Llama 3.2) | Local natural language processing |
| **Vector DB** | ChromaDB | Semantic search & embeddings |
| **Styling** | Custom CSS | Responsive, clean design |
| **HTTP** | Axios | Frontend-backend communication |

---

## Prerequisites

### **Required:**
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Node.js 16+ ([Download](https://nodejs.org/))
- Ollama + Llama 3.2 model ([Download Ollama](https://ollama.ai))

### **Verify Installation:**

```bash
# Check Python
python --version

# Check Node
node --version

# Check Ollama (must be running)
curl http://localhost:11434/api/tags
```

---

## Quick Start 

### **1. Clone & Navigate**

```bash
cd "path/to/prod assistant"
```

### **2. Start Ollama Service** (in a separate terminal)

```bash
ollama serve
# Wait for: "Listening on..."
```

### **3. Backend Setup**

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run pre-flight checks
python start_backend.py

# Start Flask API (in another terminal)
python -m flask run --port 5000
# Or: python app.py
```

**Output should show:**
```
✓ Configuration: PASS
✓ Ollama Service: PASS
✓ Database: PASS
✓ ChromaDB: PASS
Starting Productivity Assistant API
Listening on http://localhost:5000
```

### **4. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# Launches: http://localhost:3000
```

### **5. Open Browser**

```
http://localhost:3000
```

**You're ready to go!**

---

## How It Works

### **Adding a Task**

1. Go to **Dashboard** or **Productivity App** page
2. Type naturally in the input box:
   - *"Buy groceries Saturday morning"*
   - *"Call mom at 3 PM tomorrow"*
   - *"Remember to submit report by Friday"*
3. Press **Submit** or Enter
4. AI extracts: type, date, priority, tags automatically
5. Task appears in your list instantly

### **Filtering & Organizing**

- **Filter Tabs** - View by type (Tasks/Notes/Reminders) or priority
- **Search** - Semantic search finds tasks by meaning:
  - Search: *"shopping"* → finds "Buy milk", "Get groceries"
  - Search: *"meetings"* → finds all calendar events
- **Mark Complete** - Click checkbox to toggle completion

### **Viewing Your Day**

- Navigate to **Visual Day** page
- See timeline view of all tasks/reminders for today
- Color-coded by priority (High/Medium/Low)

### **Sync External Data** (Coming Soon)

- Click **Sync** button to pull from:
  -  Google Calendar events
  -  Gmail inbox tasks
  - (Currently uses mock data for demo)

---

##  API Endpoints

### **Core Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Check backend status |
| `POST` | `/api/parse` | Parse natural language input |
| `GET` | `/api/items` | Get all tasks (optional: `?type=task`) |
| `GET` | `/api/items/grouped` | Get tasks grouped by date |
| `GET` | `/api/items/search` | Semantic search: `?q=shopping` |
| `PUT` | `/api/items/<id>` | Update item (e.g., mark complete) |
| `DELETE` | `/api/items/<id>` | Delete item |
| `POST` | `/api/sync` | Sync external data (Calendar, Email) |
| `POST` | `/api/visualize/day` | Generate visual day view |


---

## 🐛 Troubleshooting

### **Ollama not connecting**

```bash
# Make sure Ollama is running
ollama serve

# Check it's accessible
curl http://localhost:11434/api/tags

# Pull the model if missing
ollama pull llama3.2
```
### **Frontend can't reach backend**

```bash
# Check Flask is running on port 5000
curl http://localhost:5000/health

# Check vite.config.js proxy:
# {
#   proxy: {
#     '/api': {
#       target: 'http://localhost:5000'
#     }
#   }
# }
```

---

## Future Enhancements

- Real-time Google Calendar integration for two-way sync
- Email task extraction from Gmail
- Notification and reminder system
- Dark mode and UI theme customization
- Mobile application support
- Multi-user authentication and authorization
- Migration to a scalable database for concurrent users
---
