# Clemson Canvas API

A simplified FastAPI application to interact with Clemson Canvas courses.

## Overview

This API provides endpoints to:
- Get a list of courses using a Canvas token
- Download course materials
- Retrieve document lists from downloaded courses

## File Structure

```
clemson_canvas_api/
├── main.py                # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Docker ignore file
├── course_data/           # Storage for downloaded course data
└── README.md              # This documentation file
```

## Running the Container

### Quick Start

```bash
# Create the course_data directory
mkdir -p course_data

# Build and start the container
docker compose up -d

# View logs
docker compose logs -f
```

The API will be accessible at http://localhost:8012

### Rebuilding After Changes

```bash
# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

## API Documentation

Once the application is running, view the interactive API documentation at:

- Swagger UI: http://localhost:8012/docs
- ReDoc: http://localhost:8012/redoc

## API Endpoints

- `GET /`: Welcome message
- `POST /get_courses`: Get all courses for a user
  - Request body: `{"token": "your_canvas_token"}`
- `POST /download_course`: Download a specific course's materials
  - Request body: `{"user_id": "user123", "course_id": 12345, "token": "your_canvas_token"}`
- `POST /get_documents`: Get list of documents in a downloaded course
  - Request body: `{"user_id": "user123", "course_id": 12345}`

## Example Usage

### Using curl

```bash
# Get courses
curl -X POST http://localhost:8012/get_courses \
  -H "Content-Type: application/json" \
  -d '{"token": "your_canvas_token"}'

# Download a course
curl -X POST http://localhost:8012/download_course \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "course_id": 12345, "token": "your_canvas_token"}'

# Get documents
curl -X POST http://localhost:8012/get_documents \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "course_id": 12345}'
```

### Using Python requests

```python
import requests
import json

# Base URL
base_url = "http://localhost:8012"

# Get courses
response = requests.post(
    f"{base_url}/get_courses", 
    json={"token": "your_canvas_token"}
)
print(json.dumps(response.json(), indent=2))

# Download a course
response = requests.post(
    f"{base_url}/download_course",
    json={
        "user_id": "user123",
        "course_id": 12345,
        "token": "your_canvas_token"
    }
)
print(response.json())
```

## Implementation Details

This implementation uses the Canvas REST API directly via the requests library instead of relying on external modules like canvasapi. This approach provides several benefits:

1. Fewer dependencies to manage
2. Direct control over API requests and responses
3. Simplified error handling
4. No issues with interactive prompts from external libraries

The downside is that it doesn't provide all the functionality of the original ClemsonCanvasGrab class, but it covers the core features needed for the API endpoints.

## Troubleshooting

- **Course Download Issues**: Check that your Canvas token has the necessary permissions
- **File Storage**: All files are stored in the `course_data` directory, which is mounted as a volume
- **API Errors**: Check the logs with `docker compose logs -f` for detailed error messages