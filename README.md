# Sales CRM

A production-ready Sales CRM application using FastAPI, Jinja2, SQLAlchemy, and SQLite.

## Features
*   **Kanban Board**: Visualize sales pipeline stages.
*   **Contact Management**: Create, edit, and track contacts.
*   **Activity Log**: Log calls, emails, and meetings for each contact.
*   **Competitive Intel**: dedicated view for analyzing competitor information.

## Tech Stack
*   **FastAPI**: High-performance web framework.
*   **Jinja2**: Templating engine.
*   **SQLAlchemy**: Database ORM.
*   **SQLite**: Lightweight database.
*   **Docker**: Containerization.

## Running with Docker

1.  Build the image:
    ```bash
    docker build -t sales-crm .
    ```

2.  Run the container:
    ```bash
    docker run -p 8000:8000 -v $(pwd)/data:/app/data sales-crm
    ```

3.  Access the application at `http://localhost:8000`.

## File Structure
*   `main.py`: Contains all backend logic (app, models, routes).
*   `templates/`: HTML templates.
*   `data/`: SQLite database storage.
