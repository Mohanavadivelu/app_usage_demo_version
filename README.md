
## Application Usage Demo - README

This project demonstrates an application usage tracking system with a backend API, database, and frontend components.

---

### Running the Application

#### 1. Development Mode
Run the backend server using Python directly (useful for debugging):
```bash
python main.py
```

#### 2. Production Mode
Run the backend server with Uvicorn for production deployments:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 3. Development with Auto-reload
Start the server with auto-reload enabled (restarts on code changes):
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

### API Documentation
After starting the server, you can access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Database Setup

To create a new SQLite database from the schema, run the following command in the `database/` directory:
```powershell
# This command reads the schema.sql file and creates app_usage.db
Get-Content schema.sql | sqlite3 app_usage.db
```
> **Note:** Ensure you have `sqlite3` installed and available in your system PATH.

---

## MCP (Model Context Protocol) Server Setup

To initialize and run the MCP server:
```bash
# Initialize the MCP server project
uv init mcp-server-app-usage

# Navigate to the project directory
cd mcp-server-app-usage

# Add the MCP CLI dependency
uv add "mcp[cli]"

# Run the MCP server
uv run mcp
```

---

## Project Structure

- `database/` - Database schema, sample data generator, and SQLite DB file
- `frontend/` - Frontend application (see subfolders for details)
- `mcp-server-app-usage/` - MCP server implementation
- `rest/` - REST API backend and core services

---

## Additional Notes

- For more details, see the README files in each subdirectory.
- Make sure to install all required dependencies as specified in the respective `requirements.txt` or `pyproject.toml` files.