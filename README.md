🎓 AI-Powered Teacher Guide for Learning Through Play

This project is a web application designed to help early childhood educators generate high-quality, play-based learning plans integrated with socio-emotional learning (SEL). It features a dynamic, database-driven curriculum builder for administrators and an intuitive chatbot interface for teachers — powered by Google’s Gemini LLM and LangChain.

🧰 Tech Stack

Frontend: Streamlit

Backend: Flask

LLM: Google Gemini (via langchain-google-genai)

AI Framework: LangChain (for prompt management, structured output, and RAG)

Database:

Development → SQLite (via SQLAlchemy)

Production → PostgreSQL (via SQLAlchemy)

Knowledge Base: Retrieval-Augmented Generation (RAG) with ChromaDB

Deployment: Ubuntu, Nginx, Gunicorn

🚀 Core Features

Conversational UI: Teachers interact with a chatbot to build lesson plans step-by-step.

Dynamic Curriculum Builder: Full admin panel for creating and managing curriculum components (Age Cohorts, Domains, Components, Play Types).

RAG-Powered Content: Admins can upload expert documents (PDFs, text, web links) to a Resource Library, which are automatically indexed and used by the AI for context-aware lesson generation.

Feedback Loop: Teachers rate generated plans (👍 / 👎), creating data for iterative model improvement.

Role-Based Access: Secure, separate interfaces for Teachers and Administrators.

⚙️ Local Development Setup
✅ Prerequisites

Python 3.10+

Git

🪜 Installation Guide
1. Clone the repository
git clone <your-repository-url>
cd <repository-name>

2. Create and activate a virtual environment
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Create the .env file

In the root directory, create a .env file and add your keys. Use .env.example as a reference.

GOOGLE_API_KEY=AIzaSy...
FLASK_SECRET_KEY=generate_a_strong_random_key_here
DATABASE_URL="sqlite:///app.db"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="a_strong_password_for_admin"
OAK_API_KEY="your_optional_oak_key"

▶️ Usage

You’ll need two terminals to run both backend and frontend locally.

1. Run the Backend
python -m backend.app


Flask will start at: http://127.0.0.1:5001
On the first run, it creates:

app.db

chroma_db vector store

2. Run the Frontend
streamlit run frontend/app.py


Streamlit will open at: http://localhost:8501

☁️ Production Deployment Guide (Ubuntu VM with PostgreSQL)
🧩 Prerequisites

Ubuntu 22.04 VM (AWS EC2, DigitalOcean, etc.)

Domain name (optional but recommended)

SSH access to the server

🪛 Step 1: Initial Server Setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-dev python3-venv build-essential libpq-dev nginx -y

🗃️ Step 2: Install and Configure PostgreSQL
Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

Create database and user
sudo -u postgres psql


Inside the shell:

CREATE DATABASE ltp_guide_db;
CREATE USER ltp_guide_user WITH PASSWORD 'your_strong_password';
ALTER ROLE ltp_guide_user SET client_encoding TO 'utf8';
ALTER ROLE ltp_guide_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ltp_guide_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ltp_guide_db TO ltp_guide_user;
\q

🧬 Step 3: Clone and Prepare the Application
git clone https://github.com/your-username/ai-teacher-guide.git
cd ai-teacher-guide


Create and activate the virtual environment:

python3 -m venv venv
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt
pip install psycopg2-binary gunicorn

🔐 Step 4: Configure Environment Variables for Production
nano .env


Paste:

# --- Production Database ---
DATABASE_URL="postgresql://ltp_guide_user:your_strong_password@localhost/ltp_guide_db"

# --- API Keys ---
GOOGLE_API_KEY="AIzaSy..."

# --- Flask Settings ---
FLASK_SECRET_KEY="a_new_strong_production_secret_key"

# --- Admin Credentials ---
ADMIN_EMAIL="your_production_admin_email@example.com"
ADMIN_PASSWORD="a_strong_production_admin_password"


Save and exit (Ctrl + X, then Y, then Enter).

⚙️ Step 5: Run the Backend with Gunicorn + systemd

Create a service file:

sudo nano /etc/systemd/system/ltp_backend.service


Paste:

[Unit]
Description=Gunicorn instance to serve the LTP Guide Backend
After=network.target

[Service]
User=<your_username>
Group=www-data
WorkingDirectory=/home/<your_username>/ai-teacher-guide
Environment="PATH=/home/<your_username>/ai-teacher-guide/venv/bin"
ExecStart=/home/<your_username>/ai-teacher-guide/venv/bin/gunicorn --workers 3 --bind unix:ltp_backend.sock -m 007 "backend.app:app"

[Install]
WantedBy=multi-user.target


Start and enable:

sudo systemctl start ltp_backend
sudo systemctl enable ltp_backend
sudo systemctl status ltp_backend

💻 Step 6: Run the Frontend with Streamlit + systemd

Create a service file:

sudo nano /etc/systemd/system/ltp_frontend.service


Paste:

[Unit]
Description=Streamlit instance for the LTP Guide Frontend
After=network.target

[Service]
User=<your_username>
Group=www-data
WorkingDirectory=/home/<your_username>/ai-teacher-guide
Environment="PATH=/home/<your_username>/ai-teacher-guide/venv/bin"
ExecStart=/home/<your_username>/ai-teacher-guide/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.headless true

[Install]
WantedBy=multi-user.target


Start and enable:

sudo systemctl start ltp_frontend
sudo systemctl enable ltp_frontend
sudo systemctl status ltp_frontend

🌐 Step 7: Configure Nginx as a Reverse Proxy

Create Nginx config:

sudo nano /etc/nginx/sites-available/ltp_guide


Paste:

server {
    listen 80;
    server_name your_domain_or_ip;

    # Backend API
    location /api {
        include proxy_params;
        proxy_pass http://unix:/home/<your_username>/ai-teacher-guide/ltp_backend.sock;
    }

    # Streamlit Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}


Enable and test:

sudo ln -s /etc/nginx/sites-available/ltp_guide /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

🎉 You’re Live!

Visit your domain name or VM IP in a browser to access the app.

Check logs:

sudo journalctl -u ltp_backend -f
sudo journalctl -u ltp_frontend -f
