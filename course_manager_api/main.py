from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge, Histogram, Summary
import os
import json
from typing import Dict, List, Union, Optional, Any
import requests
import tempfile
import shutil
import aiohttp
import ssl
import certifi
import asyncio
import io
import mimetypes
import datetime

# Import the module downloader functionality
from canvas_downloader import (
    download_file_async, 
    download_page_async, 
    download_assignment_async, 
    download_module_item_async,
    get_course_item_content
)

# Define Prometheus metrics
COURSE_DOWNLOADS = Counter(
    "course_data_manager_course_downloads_total",
    "Total number of course downloads",
    ["course_id"]
)

UPLOADS_TO_RAG = Counter(
    "course_data_manager_uploads_to_rag_total",
    "Total number of uploads to RAG server",
    ["status"]
)

FILE_SIZES = Histogram(
    "course_data_manager_file_sizes_bytes",
    "Distribution of file sizes in bytes",
    buckets=[1000, 10000, 100000, 1000000, 10000000]
)

ACTIVE_REQUESTS = Gauge(
    "course_data_manager_active_requests",
    "Number of currently active requests"
)

REQUEST_LATENCY = Summary(
    "course_data_manager_request_processing_seconds",
    "Time spent processing requests",
    ["endpoint"]
)

# Initialize the instrumentator before creating the app
instrumentator = Instrumentator()

app = FastAPI(title="Course Data Manager API")

# Setup Prometheus instrumentation - must be done before adding other middleware
instrumentator.instrument(app).expose(app)

# Configure CORS - more permissive to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define server URLs for RAG and ingestion services
RAG_SERVER_URL = "http://host.docker.internal:8081"  # For retrieval operations
INGESTION_SERVER_URL = "http://host.docker.internal:8082"  # For ingestion operations

# Define request models
class TokenRequest(BaseModel):
    token: str
    
class DownloadCourseRequest(BaseModel):
    course_id: int
    token: str
    user_id: Optional[str] = None  # Making user_id optional
    
class GetDocumentsRequest(BaseModel):
    course_id: int
    token: str  # Added token to get user_id
    user_id: Optional[str] = None  # Making user_id optional

class GetCourseContentRequest(BaseModel):
    course_id: int
    token: str
    content_type: str  # "course_info" or "file_list" or any other JSON file stored
    user_id: Optional[str] = None

class DownloadAndUploadRequest(BaseModel):
    url: str
    name: str
    type: str
    course_id: int
    token: str
    user_id: Optional[str] = None
    collection_name: Optional[str] = "default"  # Default to 'default' collection

class SelectedItem(BaseModel):
    """Model representing a selected item from Canvas"""
    name: str
    type: str
    id: Optional[Any] = None  # Accept any type for ID (int or str or None)
    courseId: str  # Note: camelCase to match frontend

class UploadSelectedToRAGRequest(BaseModel):
    """Model for the upload_selected_to_rag endpoint request"""
    course_id: str
    token: str
    user_id: str
    selected_items: List[SelectedItem]

class CanvasClient:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://clemson.instructure.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {token}"
        }
        # Get and cache user ID
        self.user_id = self._get_user_id()
    
    def _get_user_id(self):
        """Get the user ID for the current user"""
        url = f"{self.base_url}/users/self"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get user info: {response.text}")
        user_data = response.json()
        return user_data.get("id")
    
    def get_courses(self):
        """Get all courses for the authenticated user"""
        url = f"{self.base_url}/courses"
        params = {
            "enrollment_state": "active",
            "per_page": 100
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to get courses: {response.text}")
        return response.json()
    
    def get_course_materials(self, course_id):
        """Get materials for a specific course"""
        # Get modules
        modules_url = f"{self.base_url}/courses/{course_id}/modules"
        params = {
            "include": ["items"],
            "per_page": 100
        }
        modules_response = requests.get(modules_url, headers=self.headers, params=params)
        if modules_response.status_code != 200:
            raise Exception(f"Failed to get modules: {modules_response.text}")
        
        # Get files
        files_url = f"{self.base_url}/courses/{course_id}/files"
        files_params = {
            "per_page": 100
        }
        files_response = requests.get(files_url, headers=self.headers, params=files_params)
        if files_response.status_code != 200:
            raise Exception(f"Failed to get files: {files_response.text}")
        
        # Get pages
        pages_url = f"{self.base_url}/courses/{course_id}/pages"
        pages_params = {
            "per_page": 100
        }
        pages_response = requests.get(pages_url, headers=self.headers, params=pages_params)
        if pages_response.status_code != 200:
            raise Exception(f"Failed to get pages: {pages_response.text}")
        
        return {
            "modules": modules_response.json(),
            "files": files_response.json(),
            "pages": pages_response.json()
        }

    def download_file(self, file_url, save_path):
        """Download a file from Canvas"""
        response = requests.get(file_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        
        return save_path

async def upload_to_rag(file_path, file_name, collection_name="default"):
    """Upload a file to the RAG server using NVIDIA's new approach for knowledge base management"""
    print(f"[UPLOAD_TO_RAG] Starting upload for {file_name} from {file_path} to collection: {collection_name}")
    
    try:
        # Check if file exists and has content
        if not os.path.exists(file_path):
            print(f"[UPLOAD_TO_RAG] ERROR: File {file_path} does not exist!")
            UPLOADS_TO_RAG.labels(status="error_file_not_found").inc()
            raise FileNotFoundError(f"File {file_path} does not exist")
            
        file_size = os.path.getsize(file_path)
        print(f"[UPLOAD_TO_RAG] File size: {file_size} bytes")
        
        # Record file size metrics
        if file_size > 0:
            FILE_SIZES.observe(file_size)
        
        if file_size == 0:
            print(f"[UPLOAD_TO_RAG] ERROR: File is empty (0 bytes)")
            UPLOADS_TO_RAG.labels(status="error_empty_file").inc()
            raise ValueError("File is empty")
            
        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            if file_name.endswith('.html'):
                mime_type = 'text/html'
            else:
                mime_type = 'application/octet-stream'
        
        print(f"[UPLOAD_TO_RAG] Using mime type: {mime_type}")
        
        # Check if collection exists, if not create it
        await ensure_collection_exists(collection_name)
        
        # Create form data for request, including extraction and split options
        form_data = aiohttp.FormData()
        form_data.add_field("documents", open(file_path, 'rb'), filename=file_name, content_type=mime_type)
        
        # Add options as JSON data
        data = {
            "collection_name": collection_name,
            "extraction_options": {
                "extract_text": True,
                "extract_tables": True,
                "extract_charts": True,
                "extract_images": False,
                "extract_method": "pdfium",
                "text_depth": "page",
            },
            "split_options": {
                "chunk_size": 1024,
                "chunk_overlap": 150
            }
        }
        form_data.add_field("data", json.dumps(data), content_type="application/json")
        
        # Use the INGESTION API endpoint for document upload
        url = f"{INGESTION_SERVER_URL}/v1/documents"
        print(f"[UPLOAD_TO_RAG] Sending request to: {url}")
        
        # Set a longer timeout for larger files
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data, timeout=600) as response:
                print(f"[UPLOAD_TO_RAG] Response status: {response.status}")
                if response.status == 200:
                    response_text = await response.text()
                    print(f"[UPLOAD_TO_RAG] Upload successful: {response_text}")
                    UPLOADS_TO_RAG.labels(status="success").inc()
                    return {"status": "success", "collection_name": collection_name}
                else:
                    response_text = await response.text()
                    print(f"[UPLOAD_TO_RAG] Upload failed: {response_text}")
                    UPLOADS_TO_RAG.labels(status="error_rag_server").inc()
                    raise Exception(f"Failed to upload to RAG: {response_text}")
                
    except Exception as e:
        print(f"[UPLOAD_TO_RAG] EXCEPTION: Error uploading file {file_name} to RAG: {str(e)}")
        UPLOADS_TO_RAG.labels(status="error_exception").inc()
        import traceback
        print(traceback.format_exc())
        raise e

async def ensure_collection_exists(collection_name):
    """Make sure a collection exists, create it if it doesn't"""
    try:
        # Always make sure 'default' collection exists
        if collection_name != 'default':
            await ensure_collection_exists('default')
            
        # First, check if collection exists using the INGESTION API
        url = f"{INGESTION_SERVER_URL}/v1/collections"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    response_text = await response.text()
                    print(f"[ENSURE_COLLECTION] Failed to get collections: {response_text}")
                    raise Exception(f"Failed to get collections: {response_text}")
                
                collections_data = await response.json()
        
        # Parse the collections response based on API format
        if isinstance(collections_data, dict) and "collections" in collections_data:
            collections = collections_data.get("collections", [])
            collection_names = [c.get("collection_name") for c in collections]
        else:
            # Handle case where the API returns a list directly
            collections = collections_data if isinstance(collections_data, list) else []
            collection_names = [c for c in collections]
        
        # If collection doesn't exist, create it
        if collection_name not in collection_names:
            print(f"[ENSURE_COLLECTION] Creating collection: {collection_name}")
            create_url = f"{INGESTION_SERVER_URL}/v1/collections"
            
            # Create collection with appropriate parameters
            params = {
                "collection_type": "text",
                "embedding_dimension": 2048
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    create_url,
                    params=params,
                    json=[collection_name],
                    headers={"Content-Type": "application/json"}
                ) as create_response:
                    
                    if create_response.status != 200:
                        response_text = await create_response.text()
                        print(f"[ENSURE_COLLECTION] Failed to create collection: {response_text}")
                        raise Exception(f"Failed to create collection: {response_text}")
                    
                    print(f"[ENSURE_COLLECTION] Collection {collection_name} created successfully")
        else:
            print(f"[ENSURE_COLLECTION] Collection {collection_name} already exists")
        
        return True
    
    except Exception as e:
        print(f"[ENSURE_COLLECTION] Error ensuring collection exists: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise e


@app.post("/get_courses", response_model=Dict[str, str])
async def get_courses(request: TokenRequest):
    """
    Gets a list of all the courses the user is enrolled in with their ids and names using just the token
    """
    ACTIVE_REQUESTS.inc()
    try:
        if not request.token:
            raise HTTPException(status_code=400, detail="Missing token")
        
        try:
            client = CanvasClient(request.token)
            courses = client.get_courses()
            
            # Convert to the expected format (mapping of id to name)
            course_dict = {}
            for course in courses:
                if "name" in course:
                    course_dict[str(course["id"])] = course["name"]
            
            return course_dict
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()

@app.post("/download_course")
async def download_course(request: DownloadCourseRequest):
    """
    Downloads course materials for a specific course
    """
    # Extract parameters
    course_id = request.course_id
    token = request.token
    
    # Validate inputs
    if not course_id:
        raise HTTPException(status_code=400, detail="Missing course_id")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    # Increment active requests
    ACTIVE_REQUESTS.inc()
    
    try:
        client = CanvasClient(token)
        # Use the user_id from request if provided, otherwise use the one from the Canvas client
        user_id = request.user_id or str(client.user_id)
        
        # Create directory structure
        course_dir = f"course_data/{user_id}/{course_id}"
        os.makedirs(course_dir, exist_ok=True)
        
        # Ensure the default collection exists
        await ensure_collection_exists("default")
        
        # Get course info
        course_materials = client.get_course_materials(course_id)
        
        # Save course info
        with open(f"{course_dir}/course_info.json", "w") as f:
            json.dump(course_materials, f, indent=4)
        
        # Create file list
        file_list = []
        total_size = 0
        for file_info in course_materials.get("files", []):
            if "url" in file_info:
                file_path = f"{course_dir}/files/{file_info.get('display_name', 'unknown')}"
                file_size = file_info.get("size", 0)
                total_size += file_size
                
                if file_size > 0:
                    FILE_SIZES.observe(file_size)
                
                file_list.append({
                    "name": file_info.get("display_name", ""),
                    "path": file_path,
                    "type": file_info.get("content-type", ""),
                    "size": file_size,
                    "url": file_info.get("url", "")
                })
        
        # Save file list
        with open(f"{course_dir}/file_list.json", "w") as f:
            json.dump(file_list, f, indent=4)
        
        # Record metrics
        COURSE_DOWNLOADS.labels(course_id=str(course_id)).inc()
            
        return {
            "message": f"Course {course_id} processed successfully",
            "user_id": user_id  # Return the user_id that was used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Decrement active requests
        ACTIVE_REQUESTS.dec()

@app.post("/get_documents")
async def get_documents(request: GetDocumentsRequest):
    """
    Returns a list of all documents in a downloaded course
    """
    # Extract parameters
    course_id = request.course_id
    token = request.token
    
    # Validate inputs
    if not course_id:
        raise HTTPException(status_code=400, detail="Missing course_id")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    ACTIVE_REQUESTS.inc()
    try:
        client = CanvasClient(token)
        # Use the user_id from request if provided, otherwise use the one from the Canvas client
        user_id = request.user_id or str(client.user_id)
        
        course_id_str = str(course_id)
        
        # Get the list of files in the course directory
        course_dir = f"course_data/{user_id}/{course_id_str}"
        
        file_list_path = f"{course_dir}/file_list.json"
        if os.path.exists(file_list_path):
            with open(file_list_path) as f:
                file_list = json.load(f)
            return file_list
        else:
            # If file list doesn't exist yet, try to create it by downloading course info
            course_info_path = f"{course_dir}/course_info.json"
            if os.path.exists(course_info_path):
                with open(course_info_path) as f:
                    course_info = json.load(f)
                
                # Extract files from course info
                files = course_info.get("files", [])
                file_list = [{"name": file.get("display_name", "")} for file in files]
                
                # Save file list
                with open(file_list_path, "w") as f:
                    json.dump(file_list, f, indent=4)
                
                return file_list
            else:
                # If neither file list nor course info exists, download course info
                course_materials = client.get_course_materials(course_id)
                
                # Create directory if it doesn't exist
                os.makedirs(course_dir, exist_ok=True)
                
                # Save course info
                with open(course_info_path, "w") as f:
                    json.dump(course_materials, f, indent=4)
                
                # Extract files from course info
                files = course_materials.get("files", [])
                file_list = [{"name": file.get("display_name", "")} for file in files]
                
                # Save file list
                with open(file_list_path, "w") as f:
                    json.dump(file_list, f, indent=4)
                
                return file_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()

@app.post("/get_course_content")
async def get_course_content(request: GetCourseContentRequest):
    """
    Returns the specified JSON content from a downloaded course
    """
    # Extract parameters
    course_id = request.course_id
    token = request.token
    content_type = request.content_type
    
    # Validate inputs
    if not course_id:
        raise HTTPException(status_code=400, detail="Missing course_id")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    if not content_type:
        raise HTTPException(status_code=400, detail="Missing content_type")
    
    ACTIVE_REQUESTS.inc()
    try:
        client = CanvasClient(token)
        # Use the user_id from request if provided, otherwise use the one from the Canvas client
        user_id = request.user_id or str(client.user_id)
        
        course_id_str = str(course_id)
        
        # Map content_type to file name
        file_map = {
            "course_info": "course_info.json",
            "file_list": "file_list.json",
            # Add more mappings as needed
        }
        
        # Get the file name for the requested content type
        file_name = file_map.get(content_type)
        if not file_name:
            raise HTTPException(status_code=400, detail=f"Invalid content_type: {content_type}")
        
        # Construct the path to the JSON file
        json_path = f"course_data/{user_id}/{course_id_str}/{file_name}"
        
        # Check if the file exists
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail=f"Content not found: {content_type}")
        
        # Read and return the JSON content
        with open(json_path) as f:
            content = json.load(f)
        
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()

@app.post("/upload_selected_to_rag")
async def upload_selected_to_rag(request: UploadSelectedToRAGRequest):
    """
    Upload multiple selected Canvas items to the RAG server
    """
    print(f"[UPLOAD_SELECTED_TO_RAG] Starting request with {len(request.selected_items)} items")
    print(f"[UPLOAD_SELECTED_TO_RAG] Course ID: {request.course_id}, User ID: {request.user_id}")
    
    ACTIVE_REQUESTS.inc()
    
    try:
        course_id = request.course_id
        token = request.token
        user_id = request.user_id
        selected_items = request.selected_items
        
        if not course_id or not token or not selected_items:
            print("[UPLOAD_SELECTED_TO_RAG] ERROR: Missing required parameters")
            return {"status": "error", "message": "Missing required parameters"}
        
        success_count = 0
        failed_count = 0
        failed_items = []
        
        # Always use the default collection regardless of course
        collection_name = "default"
        
        # Process each selected item
        for i, item in enumerate(selected_items):
            print(f"[UPLOAD_SELECTED_TO_RAG] Processing item {i+1}/{len(selected_items)}: {item.name} (type: {item.type}, id: {item.id})")
            try:
                # Create a temp file for the content
                temp_file_handle, temp_file_path = tempfile.mkstemp()
                os.close(temp_file_handle)
                print(f"[UPLOAD_SELECTED_TO_RAG] Created temporary file: {temp_file_path}")
                
                # Extract values
                item_name = item.name
                item_type = item.type
                item_id = item.id  # This might be None for some items
                
                # Convert ID to string if not None
                if item_id is not None:
                    item_id = str(item_id)
                    print(f"[UPLOAD_SELECTED_TO_RAG] Converted item ID to string: {item_id}")

                # For items without an ID, like externalurl, we need a special case
                if item_type.lower() == 'externalurl' and not item_id:
                    print(f"[UPLOAD_SELECTED_TO_RAG] ExternalURL without ID. Creating HTML placeholder.")
                    html_content = f"""
                    <html>
                    <head>
                        <title>{item_name}</title>
                    </head>
                    <body>
                        <h1>{item_name}</h1>
                        <p>This is an external URL from Canvas. The content is not available for direct ingestion.</p>
                    </body>
                    </html>
                    """
                    temp_file_path += ".html"
                    with open(temp_file_path, "w") as f:
                        f.write(html_content)
                    
                    # Upload the placeholder to the collection
                    filename = f"{item_name}.html"
                    await upload_to_rag(temp_file_path, filename, collection_name)
                    success_count += 1
                    continue
                
                # Skip items with no ID
                if not item_id:
                    print(f"[UPLOAD_SELECTED_TO_RAG] Skipping item with no ID: {item_name}")
                    failed_items.append({
                        "name": item_name,
                        "error": "No content ID available"
                    })
                    failed_count += 1
                    continue
                
                # Determine the appropriate extension
                file_extension = ".html"  # Default to HTML
                
                # Rename temp file with appropriate extension
                new_temp_file_path = temp_file_path + file_extension
                os.rename(temp_file_path, new_temp_file_path)
                temp_file_path = new_temp_file_path
                print(f"[UPLOAD_SELECTED_TO_RAG] Renamed temporary file with extension: {temp_file_path}")
                
                # Get the content based on the item type
                print(f"[UPLOAD_SELECTED_TO_RAG] Fetching content from Canvas for item: {item_name} (type: {item_type}, id: {item_id})")
                try:
                    response = await get_course_item_content(
                        course_id=course_id, 
                        item_id=item_id,
                        item_type=item_type, 
                        token=token
                    )
                    print(f"[UPLOAD_SELECTED_TO_RAG] Got response from get_course_item_content, type: {type(response)}")
                except Exception as content_error:
                    print(f"[UPLOAD_SELECTED_TO_RAG] ERROR fetching content: {str(content_error)}")
                    import traceback
                    print(traceback.format_exc())
                    raise
                
                # Handle different response types
                if isinstance(response, (str, bytes)):
                    print(f"[UPLOAD_SELECTED_TO_RAG] Response is a string or bytes, length: {len(response)}")
                    with open(temp_file_path, "wb") as f:
                        f.write(response if isinstance(response, bytes) else response.encode('utf-8'))
                elif isinstance(response, Response):
                    print(f"[UPLOAD_SELECTED_TO_RAG] Response is a FastAPI Response")
                    with open(temp_file_path, "wb") as f:
                        f.write(response.body)
                else:
                    print(f"[UPLOAD_SELECTED_TO_RAG] Unexpected response type: {type(response)}")
                    with open(temp_file_path, "wb") as f:
                        if hasattr(response, 'body'):
                            f.write(response.body)
                        elif hasattr(response, 'content'):
                            f.write(response.content)
                        else:
                            # Last resort, convert to string
                            f.write(str(response).encode('utf-8'))
                
                # Check if the file has content
                file_size = os.path.getsize(temp_file_path)
                print(f"[UPLOAD_SELECTED_TO_RAG] Temporary file size: {file_size} bytes")
                
                if file_size == 0:
                    print(f"[UPLOAD_SELECTED_TO_RAG] WARNING: Temporary file is empty")
                    raise Exception("Downloaded content is empty")
                
                # Check the content to see if it's a HTML fallback or actual file content
                with open(temp_file_path, 'rb') as f:
                    first_bytes = f.read(50)  # Read first 50 bytes to check file type
                    is_html = b'<html' in first_bytes or b'<!DOCTYPE html' in first_bytes
                
                # Upload the file to the RAG server with the collection name and appropriate extension
                if is_html and file_extension != '.html':
                    # If we got HTML when we expected something else, use HTML extension
                    filename = f"{item_name}.html"
                    print(f"[UPLOAD_SELECTED_TO_RAG] Content appears to be HTML, using .html extension")
                else:
                    # Use original extension
                    filename = f"{item_name}{file_extension}"
                
                print(f"[UPLOAD_SELECTED_TO_RAG] Uploading to RAG collection '{collection_name}': {filename}")
                try:
                    rag_response = await upload_to_rag(temp_file_path, filename, collection_name)
                    print(f"[UPLOAD_SELECTED_TO_RAG] Upload successful: {rag_response}")
                except Exception as upload_error:
                    print(f"[UPLOAD_SELECTED_TO_RAG] ERROR during upload: {str(upload_error)}")
                    raise
                
                success_count += 1
                print(f"[UPLOAD_SELECTED_TO_RAG] Successfully processed item {i+1}")
                
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    print(f"[UPLOAD_SELECTED_TO_RAG] Cleaned up temporary file")
                    
            except Exception as e:
                print(f"[UPLOAD_SELECTED_TO_RAG] ERROR processing item {i+1}: {str(e)}")
                failed_items.append({
                    "name": item.name,
                    "error": str(e)
                })
                failed_count += 1
                # Continue with the next item
        
        # Update metrics
        UPLOADS_TO_RAG.labels(status="total_success").inc(success_count)
        UPLOADS_TO_RAG.labels(status="total_failure").inc(failed_count)
        
        final_result = {
            "status": "success",
            "message": f"{success_count} items to knowledge base",
            "success_count": success_count,
            "failed_items": failed_items
        }
        print(f"[UPLOAD_SELECTED_TO_RAG] Completed request: {final_result}")
        return final_result
            
    except Exception as e:
        print(f"[UPLOAD_SELECTED_TO_RAG] FATAL ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}
    finally:
        ACTIVE_REQUESTS.dec()

@app.post("/download_and_upload_to_rag")
async def download_and_upload_to_rag(request: DownloadAndUploadRequest):
    """
    Download content from Canvas and upload it to the RAG server
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    if not request.token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    # Ensure the collection exists (defaults to 'default')
    collection_name = request.collection_name
    await ensure_collection_exists(collection_name)
    
    ACTIVE_REQUESTS.inc()
    
    try:
        # Create a temporary file
        temp_file_handle, temp_file_path = tempfile.mkstemp()
        os.close(temp_file_handle)  # Close the file handle
        
        try:
            # Determine file extension based on type
            file_extension = ".txt"  # Default
            if request.type.lower() == "file":
                # Extract extension from file name
                file_extension = os.path.splitext(request.name)[1]
                if not file_extension:
                    file_extension = ".txt"
            elif request.type.lower() == "page":
                file_extension = ".md"
            elif request.type.lower() == "assignment":
                file_extension = ".md"
            elif request.type.lower() == "discussion_topic":
                file_extension = ".md"
            elif request.type.lower() == "quiz":
                file_extension = ".md"
            
            # Rename temp file with appropriate extension
            new_temp_file_path = temp_file_path + file_extension
            os.rename(temp_file_path, new_temp_file_path)
            temp_file_path = new_temp_file_path
            
            # Download the content based on its type
            if request.type.lower() == "file":
                await download_file_async(request.url, request.token, temp_file_path)
            elif request.type.lower() == "page":
                await download_page_async(request.url, request.token, temp_file_path)
            elif request.type.lower() == "assignment":
                await download_assignment_async(request.url, request.token, temp_file_path)
            else:
                await download_module_item_async(request.url, request.token, request.type, temp_file_path)
            
            # Create a file name
            file_name = request.name
            if not file_name.endswith(file_extension):
                file_name += file_extension
            
            # Get file size for metrics
            file_size = os.path.getsize(temp_file_path)
            if file_size > 0:
                FILE_SIZES.observe(file_size)
            
            # Upload to RAG with the specified collection name (defaults to "default")
            rag_response = await upload_to_rag(temp_file_path, file_name, request.collection_name)
            
            return {
                "status": "success",
                "message": f"File '{file_name}' downloaded and uploaded to the knowledge base",
                "rag_response": rag_response
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()

# Add endpoint for getting course item content directly from course_info.json
@app.get("/get_course_item")
async def get_course_item(course_id: str, content_id: str, item_type: str, token: str, filename: str = None):
    """
    Get content for a specific course item by ID and type
    """
    ACTIVE_REQUESTS.inc()
    try:
        print(f"get_course_item called with: course_id={course_id}, content_id={content_id}, item_type={item_type}")
        return await get_course_item_content(course_id, content_id, item_type, token, filename)
    finally:
        ACTIVE_REQUESTS.dec()

@app.get("/download_module_item")
async def download_module_item(course_id: str, module_id: str, item_id: str, token: str):
    """
    Download a specific module item from Canvas
    This endpoint handles downloads from course_info.json items
    """
    ACTIVE_REQUESTS.inc()
    try:
        # First, get the module item details
        api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/modules/{module_id}/items/{item_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status != 200:
                    response_text = await response.text()
                    print(f"Failed to get module item: {response_text}")
                    raise HTTPException(status_code=response.status, 
                                      detail=f"Failed to get module item: {response_text}")
                
                item_data = await response.json()
                print(f"Module item data: {json.dumps(item_data, indent=2)}")
                
                # Special handling for ExternalURL items
                if item_data.get('type') == 'ExternalUrl' or item_data.get('type') == 'ExternalURL':
                    # For external URLs, we need to grab the URL directly
                    external_url = item_data.get('external_url')
                    if external_url:
                        html_content = f"""
                        <html>
                        <head>
                            <title>{item_data.get('title', 'External Link')}</title>
                            <meta http-equiv="refresh" content="3;url={external_url}" />
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; text-align: center; }}
                                h1 {{ color: #2d3b45; }}
                                .container {{ margin-top: 50px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h1>{item_data.get('title', 'External Link')}</h1>
                                <p>This content is available at: <a href="{external_url}">{external_url}</a></p>
                                <p>You will be redirected to this URL in 3 seconds.</p>
                            </div>
                        </body>
                        </html>
                        """
                        
                        filename = f"{item_data.get('title', 'external_link').replace(' ', '_')}.html"
                        
                        return Response(
                            content=html_content,
                            media_type="text/html",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                        )
                
                # Extract content details
                content_id = item_data.get('content_id')
                item_type = item_data.get('type')
                title = item_data.get('title')
                
                if not content_id:
                    # For items like SubHeader that don't have content ID
                    if item_type == 'SubHeader':
                        # Return a simple text for SubHeader
                        return Response(
                            content=f"# {title}",
                            media_type="text/plain",
                            headers={"Content-Disposition": f'attachment; filename="{title}.txt"'}
                        )
                    raise HTTPException(status_code=400, detail=f"No content ID found for module item {item_id}")
                
                # Download the content based on its type
                return await get_course_item_content(course_id, content_id, item_type, token, f"{title}.html")
                
    except Exception as e:
        # Log any exceptions for debugging
        import traceback
        traceback.print_exc()
        
        # Return a user-friendly error
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()
        
@app.get("/user_info")
async def get_user_info(token: str):
    """
    Get information about the current user
    """
    ACTIVE_REQUESTS.inc()
    try:
        if not token:
            raise HTTPException(status_code=400, detail="Missing token")
        
        try:
            client = CanvasClient(token)
            return {
                "user_id": client.user_id,
                "message": "User info retrieved successfully"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_REQUESTS.dec()

@app.get("/metrics/health")
async def metrics_health():
    """
    Simple health check endpoint for monitoring
    """
    return {
        "status": "ok",
        "service": "course_data_manager",
        "timestamp": str(datetime.datetime.now())
    }

@app.get("/metrics/stats")
async def metrics_stats():
    """
    Return basic statistics about the service
    """
    import glob
    
    # Count total courses downloaded
    course_dirs = glob.glob("course_data/*/*")
    total_courses = len(course_dirs)
    
    # Count total files processed
    file_count = 0
    total_file_size = 0
    for course_dir in course_dirs:
        file_list_path = f"{course_dir}/file_list.json"
        if os.path.exists(file_list_path):
            try:
                with open(file_list_path) as f:
                    file_list = json.load(f)
                    file_count += len(file_list)
                    for file_info in file_list:
                        total_file_size += file_info.get("size", 0)
            except:
                pass
    
    return {
        "total_courses": total_courses,
        "total_files": file_count,
        "total_file_size_bytes": total_file_size,
        "active_requests": ACTIVE_REQUESTS._value.get(),
    }

@app.get("/")
async def index():
    return {"message": "Course Data Manager API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=True)