# Item Processing API

A comprehensive FastAPI application demonstrating a full CRUD (Create, Read, Update, Delete) API for managing tech products. It includes a data processing endpoint to calculate scores and provide analytics.

## Features

*   **Full CRUD Functionality**: Create, read, update, and delete items.
*   **Database Integration**: Uses SQLite with SQLAlchemy ORM.
*   **Automatic Data Seeding**: Populates the database with sample tech products on first run.
*   **Data Validation**: Leverages Pydantic for robust request and response validation.
*   **Advanced Processing**: A `/process` endpoint that calculates a custom score for each item and provides aggregate statistics.
*   **Filtering**: The `/process` endpoint supports filtering by category.
*   **Interactive Documentation**: Automatic, interactive API documentation provided by Swagger UI (`/docs`).
*   **Development Utilities**: Includes a `/reset-database` endpoint for easy development and testing.

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