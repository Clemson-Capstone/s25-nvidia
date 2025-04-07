# Course Manager API

## Overview

The Course Manager API is a microservice component of the larger S25-NVIDIA project that provides a RESTful interface for managing Canvas course data. It allows users to authenticate with their Canvas token, retrieve course listings, download course materials, and seamlessly integrate with a Retrieval Augmented Generation (RAG) server for AI-powered content processing.

## Features

- **Canvas Integration**: Secure authentication and data retrieval from Clemson Canvas LMS
- **Course Management**: Download and organize course materials by user and course
- **Document Management**: Retrieve and process various document types (assignments, quizzes, pages, discussions)
- **RAG Integration**: Upload course materials to a knowledge base for AI processing
- **Metrics & Monitoring**: Prometheus instrumentation for comprehensive performance monitoring
- **Container-Ready**: Fully containerized for easy deployment and scaling

## Architecture

This service uses FastAPI for the API framework, providing async capabilities for efficient concurrent connections to Canvas and the RAG server. It integrates with Prometheus for monitoring and uses Docker for containerization.

### Component Diagram

```
┌───────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│                   │    │                     │    │                  │
│   Course Manager  │◄───┤   Canvas LMS API    │    │    RAG Server    │
│       API         │    │                     │    │                  │
│                   │    └─────────────────────┘    │                  │
└───────┬───────────┘                               └─────────┬────────┘
        │                                                     │
        │                                                     │
        └─────────────────────►───────────────────────────────┘
                       Document Upload Flow
```

## Technical Specifications

### Dependencies

| Package                            | Version      | Purpose                                    |
|------------------------------------|--------------|-------------------------------------------|
| fastapi                            | >=0.115.2    | Web framework for building APIs            |
| uvicorn                            | >=0.23.2     | ASGI server implementation                 |
| pydantic                           | 2.9.2        | Data validation and settings management    |
| python-multipart                   | 0.0.20       | Support for multipart/form-data            |
| requests                           | 2.32.3       | HTTP requests for the Canvas API           |
| aiohttp                            | 3.11.16      | Async HTTP requests for improved performance|
| certifi                            | 2025.1.31    | Certificate verification                   |
| prometheus-client                  | 0.21.1       | Instrumentation client library             |
| prometheus-fastapi-instrumentator  | 7.1.0        | FastAPI-specific Prometheus integration    |

### File Structure

```
course_manager_api/
├── main.py                # Main FastAPI application with routes and core logic
├── canvas_downloader.py   # Module for downloading content from Canvas
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── .dockerignore          # Docker build exclusions
├── .gitignore             # Git exclusions
└── README.md              # This documentation file
```

### Metrics Collected

The API implements comprehensive monitoring with the following Prometheus metrics:

- **Counter**: `course_data_manager_course_downloads_total` - Number of course downloads by course ID
- **Counter**: `course_data_manager_uploads_to_rag_total` - Success/failure counts for RAG uploads
- **Histogram**: `course_data_manager_file_sizes_bytes` - Distribution of processed file sizes
- **Gauge**: `course_data_manager_active_requests` - Number of concurrent active requests
- **Summary**: `course_data_manager_request_processing_seconds` - Request latency by endpoint

## API Endpoints

### User Authentication

- `GET /user_info` - Get user information from Canvas token
  - Query parameter: `token` (Canvas API token)

### Course Management

- `POST /get_courses` - Get all courses for a user
  - Request body: `{"token": "your_canvas_token"}`

- `POST /download_course` - Download a course's materials
  - Request body: `{"course_id": 12345, "token": "your_canvas_token", "user_id": "optional"}`

- `POST /get_documents` - Get documents in a downloaded course
  - Request body: `{"course_id": 12345, "token": "your_canvas_token", "user_id": "optional"}`

- `POST /get_course_content` - Get specific JSON content for a course
  - Request body: `{"course_id": 12345, "token": "your_canvas_token", "content_type": "course_info|file_list", "user_id": "optional"}`

### Content Retrieval

- `GET /get_course_item` - Get specific course item content
  - Query parameters: `course_id`, `content_id`, `item_type`, `token`, `filename` (optional)

- `GET /download_module_item` - Download a specific module item
  - Query parameters: `course_id`, `module_id`, `item_id`, `token`

### RAG Integration

- `POST /upload_selected_to_rag` - Upload selected Canvas items to RAG
  - Request body with course/user details and array of selected items

- `POST /download_and_upload_to_rag` - Download and upload a single item
  - Request body with item details including URL, name, type, course ID, token

### Monitoring

- `GET /metrics/health` - Health check endpoint
- `GET /metrics/stats` - Basic service statistics
- Prometheus metrics available at default endpoint

## Running the Service

### Docker Environment

The API is containerized using Docker:

```bash
# Build the image
docker build -t course-manager-api .

# Run the container
docker run -d -p 8012:8012 -v $(pwd)/course_data:/app/course_data --name course-manager-api course-manager-api
```

### Configuration

The service connects to the following external components:

- **Canvas LMS**: Authentication via token-based authentication
- **RAG Server**: Configured via `RAG_SERVER_URL` (default: "http://host.docker.internal:8081")

### Volume Mounts

- `/app/course_data`: Persistent storage for downloaded course materials

## Security Considerations

- API uses token-based authentication from Canvas
- No credentials are stored in the API; tokens are passed per request
- Host-specific paths are isolated within Docker container
- API requires explicit consent for operations that modify data

## Integration Points

This module is designed as part of a larger system with the following integration points:

1. **Canvas LMS**: RESTful API integration via token-based authentication
2. **RAG Server**: HTTP-based document upload for knowledge base integration
3. **Frontend Applications**: API consumption for web/mobile interfaces

## Troubleshooting

- **Canvas Authentication Issues**: Verify token permissions and expiration
- **File Download Problems**: Check Canvas file access permissions
- **RAG Integration Errors**: Ensure RAG server is running and accessible
- **Storage Issues**: Check volume mount paths and permissions

## Example Usage

### Bash/cURL

```bash
# Get user info
curl -X GET "http://localhost:8012/user_info?token=your_canvas_token"

# Get courses
curl -X POST http://localhost:8012/get_courses \
  -H "Content-Type: application/json" \
  -d '{"token": "your_canvas_token"}'

# Download course
curl -X POST http://localhost:8012/download_course \
  -H "Content-Type: application/json" \
  -d '{"course_id": 12345, "token": "your_canvas_token"}'
```

### Python

```python
import requests
import json

base_url = "http://localhost:8012"
token = "your_canvas_token"

# Get user info
response = requests.get(f"{base_url}/user_info", params={"token": token})
user_data = response.json()
user_id = user_data["user_id"]

# Get courses
response = requests.post(f"{base_url}/get_courses", json={"token": token})
courses = response.json()

# Download a course
course_id = next(iter(courses.keys()))
response = requests.post(
    f"{base_url}/download_course",
    json={"course_id": int(course_id), "token": token}
)
```

## Maintainers

This module is part of the S25-NVIDIA project.

## License

Refer to the main project repository for license information.
