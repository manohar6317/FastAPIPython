# Item Processing API

This is a simple FastAPI project that demonstrates database interaction with SQLAlchemy, data seeding, and a processing endpoint.

The API provides one endpoint, `/process`, which calculates a score for each item in the database and returns the top-scoring items along with aggregate statistics.

## Setup and Run

Follow these steps to get the application running.

### 1. Create and Activate a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```
> **Note:** If you are using the older Command Prompt (`cmd.exe`) on Windows, the activation command is `venv\Scripts\activate`.

### 2. Install Dependencies

Install the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt