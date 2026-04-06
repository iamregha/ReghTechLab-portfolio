# Getting Started

This guide will help you set up the ReghTechLab portfolio app on your local machine for development and testing.

## Prerequisites

- Python 3.8+
- `pip` (Python package installer)

## Installation

1. **Clone the repository** (if you haven't already).
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment:**
   - **Windows:** `venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses an SQLite database (`portfolio.db`) by default.
It relies on environmental variables, primarily `SECRET_KEY`, which defaults to a development string if not provided.

## Running the App

Start the Flask development server:

```bash
python app.py
```

The app will become available at `http://127.0.0.1:5000/`.

> **Note:** The SQLite database and all necessary tables will be created automatically the first time you run `app.py`.
