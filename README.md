# AI-Powered Teacher Guide for Learning Through Play

This project is a web application designed to help early childhood educators generate high-quality, play-based learning plans integrated with socio-emotional learning (SEL). It features a dynamic, database-driven curriculum builder for administrators and an intuitive chatbot interface for teachers.

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Flask
- **LLM:** Google Gemini (via `langchain-google-genai`)
- **AI Framework:** LangChain (for prompt management and structured output)
- **Database:** SQLAlchemy with SQLite (for development)
- **Knowledge Base:** Retrieval-Augmented Generation (RAG) with ChromaDB

## Features

- **Conversational UI:** Teachers interact with a chatbot to build lesson plans step-by-step.
- **Dynamic Curriculum Builder:** A full admin panel allows for creating and managing all curriculum components (Age Cohorts, Domains, Components, Play Types).
- **RAG-Powered Content:** An admin-managed "Resource Library" allows uploading expert documents (PDFs, text) which are used to generate context-aware, high-quality plans.
- **Feedback Loop:** Teachers can rate generated plans, creating a dataset for future fine-tuning.
- **Role-Based Access:** Separate, secure interfaces for Teachers and Administrators.

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create the `.env` file:**
    In the root directory, create a file named `.env` and add your secret keys. Use `.env.example` as a template.
    ```.env
    GOOGLE_API_KEY="AIzaSy..."
    FLASK_SECRET_KEY="a_strong_random_key"
    DATABASE_URL="sqlite:///app.db"
    ADMIN_EMAIL="admin@example.com"
    ADMIN_PASSWORD="your_admin_password"
    ```

### Usage

You will need two separate terminals to run the application.

1.  **Run the Backend Server:**
    ```bash
    python -m backend.app
    ```
    The Flask server will start on `http://127.0.0.1:5001`. On the first run, it will create the `app.db` file and the `chroma_db` vector store.

2.  **Run the Frontend Application:**
    ```bash
    streamlit run frontend/app.py
    ```
    The Streamlit app will open in your browser at `http://localhost:8501`.