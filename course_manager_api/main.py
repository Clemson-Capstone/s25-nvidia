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

# Set environment variables for image captioning
os.environ["APP_NVINGEST_EXTRACTIMAGES"] = "True"
os.environ["VLM_CAPTION_ENDPOINT"] = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions"
os.environ["VLM_CAPTION_MODEL_NAME"] = "meta/llama-3.2-11b-vision-instruct"
os.environ["VLM_USE_LOCAL_SERVICE"] = "False"  # Ensure we're not trying to use a local service

# Log the image captioning configuration
print(f"[IMAGE_CAPTIONING] Enabled with endpoint: {os.environ.get('VLM_CAPTION_ENDPOINT')}")
print(f"[IMAGE_CAPTIONING] Model: {os.environ.get('VLM_CAPTION_MODEL_NAME')}")
print(f"[IMAGE_CAPTIONING] Using local service: {os.environ.get('VLM_USE_LOCAL_SERVICE')}")

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
        print("[CANVAS_CLIENT] Initializing CanvasClient")
        self.token = token
        self.base_url = "https://clemson.instructure.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {token}"
        }
        print(f"[CANVAS_CLIENT] Base URL: {self.base_url}")
        print(f"[CANVAS_CLIENT] Token length: {len(token)}")
        print(f"[CANVAS_CLIENT] Headers: {self.headers}")
        
        # Get and cache user ID
        print("[CANVAS_CLIENT] Getting user ID")
        self.user_id = self._get_user_id()
        print(f"[CANVAS_CLIENT] User ID obtained: {self.user_id}")
    
    def _get_user_id(self):
        """Get the user ID for the current user"""
        url = f"{self.base_url}/users/self"
        print(f"[CANVAS_CLIENT] Fetching user info from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            print(f"[CANVAS_CLIENT] User info response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[CANVAS_CLIENT] Failed to get user info: {error_text}")
                raise Exception(f"Failed to get user info: {error_text}")
            
            user_data = response.json()
            print(f"[CANVAS_CLIENT] User data keys: {list(user_data.keys())}")
            user_id = user_data.get("id")
            
            if not user_id:
                print(f"[CANVAS_CLIENT] WARNING: No user ID found in response: {user_data}")
            
            return user_id
        except Exception as e:
            print(f"[CANVAS_CLIENT] EXCEPTION in _get_user_id: {str(e)}")
            import traceback
            print(f"[CANVAS_CLIENT] Traceback: {traceback.format_exc()}")
            raise
    
    def get_courses(self):
        """Get all courses for the authenticated user"""
        url = f"{self.base_url}/courses"
        params = {
            "enrollment_state": "active",
            "per_page": 100
        }
        print(f"[CANVAS_CLIENT] Fetching courses from: {url} with params: {params}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            print(f"[CANVAS_CLIENT] Courses response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[CANVAS_CLIENT] Failed to get courses: {error_text}")
                raise Exception(f"Failed to get courses: {error_text}")
            
            courses = response.json()
            print(f"[CANVAS_CLIENT] Retrieved {len(courses)} courses")
            return courses
        except Exception as e:
            print(f"[CANVAS_CLIENT] EXCEPTION in get_courses: {str(e)}")
            import traceback
            print(f"[CANVAS_CLIENT] Traceback: {traceback.format_exc()}")
            raise
    
    def get_course_materials(self, course_id):
        """Get materials for a specific course"""
        print(f"[CANVAS_CLIENT] Starting get_course_materials for course_id={course_id}")
        result = {}
        
        try:
            # Get modules
            modules_url = f"{self.base_url}/courses/{course_id}/modules"
            params = {
                "include": ["items"],
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching modules from: {modules_url} with params: {params}")
            
            try:
                modules_response = requests.get(modules_url, headers=self.headers, params=params)
                print(f"[CANVAS_CLIENT] Modules response status: {modules_response.status_code}")
                
                if modules_response.status_code == 200:
                    modules_data = modules_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(modules_data)} modules")
                    
                    # Log module structure to understand what we're getting
                    if len(modules_data) > 0:
                        sample_module = modules_data[0]
                        print(f"[CANVAS_CLIENT] Sample module keys: {list(sample_module.keys())}")
                        
                        # Log items in the first module for debugging
                        if 'items' in sample_module and len(sample_module['items']) > 0:
                            print(f"[CANVAS_CLIENT] Module contains {len(sample_module['items'])} items")
                            sample_item = sample_module['items'][0]
                            print(f"[CANVAS_CLIENT] Sample module item keys: {list(sample_item.keys())}")
                            print(f"[CANVAS_CLIENT] Sample module item: {sample_item}")
                    
                    result["modules"] = modules_data
                else:
                    error_text = modules_response.text
                    print(f"[CANVAS_CLIENT] Failed to get modules: {error_text}")
                    # Continue with other API calls but record the error
                    result["modules"] = []
                    result["modules_error"] = f"Status code: {modules_response.status_code}, Error: {error_text}"
            except Exception as modules_error:
                print(f"[CANVAS_CLIENT] ERROR fetching modules: {str(modules_error)}")
                import traceback
                print(f"[CANVAS_CLIENT] Modules traceback: {traceback.format_exc()}")
                # Continue with other API calls but record the error
                result["modules"] = []
                result["modules_error"] = str(modules_error)
            
            # Get files
            files_url = f"{self.base_url}/courses/{course_id}/files"
            files_params = {
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching files from: {files_url} with params: {files_params}")
            
            try:
                files_response = requests.get(files_url, headers=self.headers, params=files_params)
                print(f"[CANVAS_CLIENT] Files response status: {files_response.status_code}")
                
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(files_data)} files")
                    
                    # Log file structure
                    if len(files_data) > 0:
                        sample_file = files_data[0]
                        print(f"[CANVAS_CLIENT] Sample file keys: {list(sample_file.keys())}")
                        print(f"[CANVAS_CLIENT] Sample file: id={sample_file.get('id')}, name={sample_file.get('display_name')}, type={sample_file.get('content-type')}")
                        print(f"[CANVAS_CLIENT] Sample file has URL: {'url' in sample_file}")
                    
                    result["files"] = files_data
                else:
                    error_text = files_response.text
                    print(f"[CANVAS_CLIENT] Failed to get files: {error_text}")
                    # Continue with other API calls but record the error
                    result["files"] = []
                    result["files_error"] = f"Status code: {files_response.status_code}, Error: {error_text}"
            except Exception as files_error:
                print(f"[CANVAS_CLIENT] ERROR fetching files: {str(files_error)}")
                import traceback
                print(f"[CANVAS_CLIENT] Files traceback: {traceback.format_exc()}")
                # Continue with other API calls but record the error
                result["files"] = []
                result["files_error"] = str(files_error)
            
            # Get pages - THIS IS WHERE THE ISSUE MIGHT BE WITH COURSES THAT DON'T HAVE PAGES
            pages_url = f"{self.base_url}/courses/{course_id}/pages"
            pages_params = {
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching pages from: {pages_url} with params: {pages_params}")
            
            try:
                pages_response = requests.get(pages_url, headers=self.headers, params=pages_params)
                pages_status = pages_response.status_code
                print(f"[CANVAS_CLIENT] Pages response status: {pages_status}")
                
                # Check specifically for no pages, which might return 404 or empty list
                if pages_status == 200:
                    pages_data = pages_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(pages_data)} pages")
                    
                    # Log page structure
                    if len(pages_data) > 0:
                        sample_page = pages_data[0]
                        print(f"[CANVAS_CLIENT] Sample page keys: {list(sample_page.keys())}")
                    
                    result["pages"] = pages_data
                elif pages_status == 404:
                    # This course doesn't have pages feature enabled
                    print(f"[CANVAS_CLIENT] Pages feature not enabled for this course (404)")
                    result["pages"] = []
                    result["pages_error"] = "Pages feature not enabled for this course"
                else:
                    error_text = pages_response.text
                    print(f"[CANVAS_CLIENT] Failed to get pages: {error_text}")
                    # Continue with other API calls but record the error
                    result["pages"] = []
                    result["pages_error"] = f"Status code: {pages_status}, Error: {error_text}"
            except Exception as pages_error:
                print(f"[CANVAS_CLIENT] ERROR fetching pages: {str(pages_error)}")
                import traceback
                print(f"[CANVAS_CLIENT] Pages traceback: {traceback.format_exc()}")
                # Continue with other API calls but record the error
                result["pages"] = []
                result["pages_error"] = str(pages_error)
            
            # Try to get assignments as well
            assignments_url = f"{self.base_url}/courses/{course_id}/assignments"
            assignments_params = {
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching assignments from: {assignments_url} with params: {assignments_params}")
            
            try:
                assignments_response = requests.get(assignments_url, headers=self.headers, params=assignments_params)
                assignments_status = assignments_response.status_code
                print(f"[CANVAS_CLIENT] Assignments response status: {assignments_status}")
                
                if assignments_status == 200:
                    assignments_data = assignments_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(assignments_data)} assignments")
                    result["assignments"] = assignments_data
                elif assignments_status == 401:
                    # Unauthorized - maybe the course is inactive or user doesn't have access
                    print(f"[CANVAS_CLIENT] Unauthorized access to assignments (401)")
                    result["assignments"] = []
                    result["assignments_error"] = "Unauthorized access to assignments"
                elif assignments_status == 404:
                    # This course doesn't have assignments feature enabled
                    print(f"[CANVAS_CLIENT] Assignments feature not enabled for this course (404)")
                    result["assignments"] = []
                    result["assignments_error"] = "Assignments feature not enabled for this course"
                else:
                    error_text = assignments_response.text
                    print(f"[CANVAS_CLIENT] Failed to get assignments: {error_text}")
                    # Continue with other API calls but record the error
                    result["assignments"] = []
                    result["assignments_error"] = f"Status code: {assignments_status}, Error: {error_text}"
            except Exception as assignments_error:
                print(f"[CANVAS_CLIENT] ERROR fetching assignments: {str(assignments_error)}")
                import traceback
                print(f"[CANVAS_CLIENT] Assignments traceback: {traceback.format_exc()}")
                result["assignments"] = []
                result["assignments_error"] = str(assignments_error)
            
            # Try to get quizzes as well
            quizzes_url = f"{self.base_url}/courses/{course_id}/quizzes"
            quizzes_params = {
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching quizzes from: {quizzes_url} with params: {quizzes_params}")
            
            try:
                quizzes_response = requests.get(quizzes_url, headers=self.headers, params=quizzes_params)
                quizzes_status = quizzes_response.status_code
                print(f"[CANVAS_CLIENT] Quizzes response status: {quizzes_status}")
                
                if quizzes_status == 200:
                    quizzes_data = quizzes_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(quizzes_data)} quizzes")
                    result["quizzes"] = quizzes_data
                elif quizzes_status == 401:
                    # Unauthorized - maybe the course is inactive or user doesn't have access
                    print(f"[CANVAS_CLIENT] Unauthorized access to quizzes (401)")
                    result["quizzes"] = []
                    result["quizzes_error"] = "Unauthorized access to quizzes"
                elif quizzes_status == 404:
                    # This course doesn't have quizzes feature enabled
                    print(f"[CANVAS_CLIENT] Quizzes feature not enabled for this course (404)")
                    result["quizzes"] = []
                    result["quizzes_error"] = "Quizzes feature not enabled for this course"
                else:
                    error_text = quizzes_response.text
                    print(f"[CANVAS_CLIENT] Failed to get quizzes: {error_text}")
                    # Continue with other API calls but record the error
                    result["quizzes"] = []
                    result["quizzes_error"] = f"Status code: {quizzes_status}, Error: {error_text}"
            except Exception as quizzes_error:
                print(f"[CANVAS_CLIENT] ERROR fetching quizzes: {str(quizzes_error)}")
                import traceback
                print(f"[CANVAS_CLIENT] Quizzes traceback: {traceback.format_exc()}")
                result["quizzes"] = []
                result["quizzes_error"] = str(quizzes_error)
            
            # Try to get discussion topics as well (another common Canvas component)
            discussions_url = f"{self.base_url}/courses/{course_id}/discussion_topics"
            discussions_params = {
                "per_page": 100
            }
            print(f"[CANVAS_CLIENT] Fetching discussion topics from: {discussions_url} with params: {discussions_params}")
            
            try:
                discussions_response = requests.get(discussions_url, headers=self.headers, params=discussions_params)
                discussions_status = discussions_response.status_code
                print(f"[CANVAS_CLIENT] Discussions response status: {discussions_status}")
                
                if discussions_status == 200:
                    discussions_data = discussions_response.json()
                    print(f"[CANVAS_CLIENT] Retrieved {len(discussions_data)} discussion topics")
                    result["discussions"] = discussions_data
                elif discussions_status in [401, 403, 404]:
                    # This course might not have discussions enabled or accessible
                    print(f"[CANVAS_CLIENT] Discussions feature not available: {discussions_status}")
                    result["discussions"] = []
                    result["discussions_error"] = f"Discussions feature not available: {discussions_status}"
                else:
                    error_text = discussions_response.text
                    print(f"[CANVAS_CLIENT] Failed to get discussions: {error_text}")
                    result["discussions"] = []
                    result["discussions_error"] = f"Status code: {discussions_status}, Error: {error_text}"
            except Exception as discussions_error:
                print(f"[CANVAS_CLIENT] ERROR fetching discussions: {str(discussions_error)}")
                result["discussions"] = []
                result["discussions_error"] = str(discussions_error)
            
            print(f"[CANVAS_CLIENT] Completed get_course_materials for course_id={course_id}")
            # Return the result even if some components failed
            return result
            
        except Exception as e:
            print(f"[CANVAS_CLIENT] FATAL ERROR in get_course_materials: {str(e)}")
            import traceback
            print(f"[CANVAS_CLIENT] Traceback: {traceback.format_exc()}")
            # Create minimal valid result rather than failing completely
            return {
                "modules": [],
                "files": [],
                "pages": [],
                "assignments": [],
                "quizzes": [],
                "discussions": [],
                "fatal_error": str(e)
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

def clean_filename(filename):
    """Clean a filename to fix problematic extensions like .pdf.html"""
    if not filename:
        return filename
        
    # Check if we have a double extension with .html at the end
    lower_name = filename.lower()
    
    # General patterns for detecting file extensions
    known_extensions = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.jpg', '.png', 
                       '.doc', '.xls', '.ppt', '.csv', '.zip', '.mp3', '.mp4', 
                       '.gif', '.svg', '.json', '.xml', '.md']
                    
    # If the filename ends with .html, check if there's another extension before it
    if lower_name.endswith('.html'):
        for ext in known_extensions:
            if ext + '.html' in lower_name:
                # Replace just the .html at the end of the extension
                cleaned_name = filename.replace(ext + '.html', ext)
                print(f"[CLEAN_FILENAME] Cleaned double extension: {filename} -> {cleaned_name}")
                return cleaned_name
    
    # Also handle the case where brackets or special characters got into filenames
    cleaned = filename
    # Remove URL encoding of spaces and special characters 
    if '%20' in cleaned:
        cleaned = cleaned.replace('%20', ' ')
    if '%' in cleaned and any(c.isdigit() for c in cleaned):
        # Try to clean up other URL encoded characters
        try:
            from urllib.parse import unquote
            decoded = unquote(cleaned)
            if decoded != cleaned:
                print(f"[CLEAN_FILENAME] URL decoded: {cleaned} -> {decoded}")
                cleaned = decoded
        except:
            pass
            
    return cleaned
            
async def upload_to_rag(file_path, file_name, collection_name="default"):
    """Upload a file to the RAG server using NVIDIA's new approach for knowledge base management"""
    # Clean the filename first
    file_name = clean_filename(file_name)
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
            
        # We already cleaned the filename at the function start, but let's also check content
        # Try to determine the content type from file data (magic bytes)
        content_type_from_bytes = None
        try:
            with open(file_path, 'rb') as f:
                first_bytes = f.read(8)  # Read first few bytes
                
                # Check for PDF
                if first_bytes.startswith(b'%PDF-'):
                    content_type_from_bytes = 'application/pdf'
                    print(f"[UPLOAD_TO_RAG] Content identified as PDF based on magic bytes")
                # Check for HTML
                elif first_bytes.startswith(b'<!DOCTYPE') or b'<html' in first_bytes:
                    content_type_from_bytes = 'text/html'
                    print(f"[UPLOAD_TO_RAG] Content identified as HTML based on content")
                # Check for XML
                elif first_bytes.startswith(b'<?xml'):
                    content_type_from_bytes = 'application/xml'
                    print(f"[UPLOAD_TO_RAG] Content identified as XML based on content")
                # Check for JPEG
                elif first_bytes.startswith(b'\xff\xd8\xff'):
                    content_type_from_bytes = 'image/jpeg'
                    print(f"[UPLOAD_TO_RAG] Content identified as JPEG image based on magic bytes")
                # Check for PNG
                elif first_bytes.startswith(b'\x89PNG'):
                    content_type_from_bytes = 'image/png'
                    print(f"[UPLOAD_TO_RAG] Content identified as PNG image based on magic bytes")
                # Check for GIF
                elif first_bytes.startswith(b'GIF87a') or first_bytes.startswith(b'GIF89a'):
                    content_type_from_bytes = 'image/gif'
                    print(f"[UPLOAD_TO_RAG] Content identified as GIF image based on magic bytes")
                    
                # Reset file position
                f.seek(0)
        except Exception as e:
            print(f"[UPLOAD_TO_RAG] Warning: Failed to detect content type from bytes: {str(e)}")
            
        # Determine mime type based on the cleaned file name
        mime_type, _ = mimetypes.guess_type(file_name)
        
        # If we detected a content type from bytes, it takes precedence
        if content_type_from_bytes:
            mime_type = content_type_from_bytes
        # Otherwise fallback to extension-based detection
        elif not mime_type:
            if file_name.endswith('.html'):
                mime_type = 'text/html'
            elif file_name.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif file_name.endswith('.jpeg') or file_name.endswith('.jpg'):
                mime_type = 'image/jpeg'
            elif file_name.endswith('.png'):
                mime_type = 'image/png'
            elif file_name.endswith('.gif'):
                mime_type = 'image/gif'
            else:
                mime_type = 'application/octet-stream'
        
        # Determine if this is an image file
        is_image = mime_type and mime_type.startswith('image/')
        
        print(f"[UPLOAD_TO_RAG] Using mime type: {mime_type}")
        
        # Check if collection exists, if not create it
        await ensure_collection_exists(collection_name)
        
        # Create form data for request, including extraction and split options
        form_data = aiohttp.FormData()
        form_data.add_field("documents", open(file_path, 'rb'), filename=file_name, content_type=mime_type)
        
        # Add options as JSON data
        if is_image:
            # Special handling for image files with image captioning enabled
            print(f"[UPLOAD_TO_RAG] Detected image file, enabling image captioning")
            
            # We will now pass the image directly to the RAG server with image captioning enabled
            # This enables the VLM model to extract meaningful content from the images
            # No need to create a text description file as the image captioning service will handle it
        
        # Standard extraction options with image captioning enabled
        data = {
            "collection_name": collection_name,
            "extraction_options": {
                "extract_text": True,
                "extract_tables": True,
                "extract_charts": True,
                "extract_images": True,  # Enable image extraction
                "caption_images": True,  # Enable image captioning for embedded images
                "extract_method": "pdfium",
                "text_depth": "page",
                "skip_image_extraction": False  # Don't skip image extraction
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
                    
                    # Clean up the text description file if it was created for an image
                    if is_image and file_path.endswith('.txt') and os.path.exists(temp_file_path):
                        try:
                            # Clean up both the original image and text description
                            if os.path.exists(temp_file_path):
                                print(f"[UPLOAD_TO_RAG] Removing temporary image file: {temp_file_path}")
                                os.remove(temp_file_path)
                        except Exception as cleanup_error:
                            print(f"[UPLOAD_TO_RAG] Warning: Failed to clean up temp files: {str(cleanup_error)}")
                    
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

@app.post("/download_course", response_model_exclude_none=True)
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
    
    # Start logging information
    print(f"[DOWNLOAD_COURSE] Starting download for course_id={course_id}")
    
    try:
        print(f"[DOWNLOAD_COURSE] Creating CanvasClient with token length: {len(token)}")
        client = CanvasClient(token)
        
        # Use the user_id from request if provided, otherwise use the one from the Canvas client
        user_id = request.user_id or str(client.user_id)
        print(f"[DOWNLOAD_COURSE] Using user_id: {user_id}")
        
        # Create directory structure - check parent directory first
        base_dir = "course_data"
        user_dir = f"{base_dir}/{user_id}"
        course_dir = f"{user_dir}/{course_id}"
        
        print(f"[DOWNLOAD_COURSE] Checking if base directory exists: {base_dir}")
        if not os.path.exists(base_dir):
            try:
                print(f"[DOWNLOAD_COURSE] Creating base directory: {base_dir}")
                os.mkdir(base_dir)
                print(f"[DOWNLOAD_COURSE] Successfully created base directory: {base_dir}")
            except PermissionError as pe:
                print(f"[DOWNLOAD_COURSE] ERROR: Permission denied creating {base_dir}: {str(pe)}")
                # Try to get more details about the permissions
                try:
                    import subprocess
                    ls_output = subprocess.run(["ls", "-la"], capture_output=True, text=True)
                    print(f"[DOWNLOAD_COURSE] Current directory listing: {ls_output.stdout}")
                except Exception as ls_error:
                    print(f"[DOWNLOAD_COURSE] Could not list directory: {str(ls_error)}")
                raise HTTPException(status_code=500, 
                                    detail=f"Permission error: Cannot create required directory {base_dir}. Please check file system permissions.")
            except Exception as e:
                print(f"[DOWNLOAD_COURSE] ERROR creating base directory: {str(e)}")
                raise HTTPException(status_code=500, 
                                    detail=f"Error creating directory {base_dir}: {str(e)}")
        
        # Now check and create user directory
        print(f"[DOWNLOAD_COURSE] Checking if user directory exists: {user_dir}")
        if not os.path.exists(user_dir):
            try:
                print(f"[DOWNLOAD_COURSE] Creating user directory: {user_dir}")
                os.mkdir(user_dir)
                print(f"[DOWNLOAD_COURSE] Successfully created user directory: {user_dir}")
            except PermissionError as pe:
                print(f"[DOWNLOAD_COURSE] ERROR: Permission denied creating {user_dir}: {str(pe)}")
                raise HTTPException(status_code=500, 
                                    detail=f"Permission error: Cannot create required directory {user_dir}. Please check file system permissions.")
            except Exception as e:
                print(f"[DOWNLOAD_COURSE] ERROR creating user directory: {str(e)}")
                raise HTTPException(status_code=500, 
                                    detail=f"Error creating directory {user_dir}: {str(e)}")
        
        # Finally create course directory
        print(f"[DOWNLOAD_COURSE] Creating course directory: {course_dir}")
        try:
            os.makedirs(course_dir, exist_ok=True)
            print(f"[DOWNLOAD_COURSE] Successfully created course directory: {course_dir}")
        except PermissionError as pe:
            print(f"[DOWNLOAD_COURSE] ERROR: Permission denied creating {course_dir}: {str(pe)}")
            raise HTTPException(status_code=500, 
                                detail=f"Permission error: Cannot create required directory {course_dir}. Please check file system permissions.")
        except Exception as e:
            print(f"[DOWNLOAD_COURSE] ERROR creating course directory: {str(e)}")
            raise HTTPException(status_code=500, 
                                detail=f"Error creating directory {course_dir}: {str(e)}")
        
        # Ensure the default collection exists
        print(f"[DOWNLOAD_COURSE] Ensuring default collection exists")
        await ensure_collection_exists("default")
        
        # Get course info with timeout
        print(f"[DOWNLOAD_COURSE] Fetching course materials for course_id={course_id}")
        try:
            # Add timeout tracking
            import time
            start_time = time.time()
            max_time = 60  # 60 second timeout
            
            # Create a progress tracking variable
            fetch_progress = "starting"
            print(f"[DOWNLOAD_COURSE] Progress: {fetch_progress}")
            
            # Fetch course materials with progress tracking
            fetch_progress = "getting_client"
            course_materials = {}  # Initialize in case of early failure
            
            # Implement timeout tracking for get_course_materials
            fetch_progress = "calling_get_course_materials"
            course_materials = client.get_course_materials(course_id)
            fetch_progress = "get_course_materials_completed"
            
            # Check elapsed time
            elapsed_time = time.time() - start_time
            print(f"[DOWNLOAD_COURSE] Fetched course materials in {elapsed_time:.2f} seconds")
            
            # Handle None result
            if course_materials is None:
                print(f"[DOWNLOAD_COURSE] ERROR: get_course_materials returned None")
                raise HTTPException(status_code=500, detail="Failed to retrieve course materials")
            
            fetch_progress = "processing_materials"
            print(f"[DOWNLOAD_COURSE] Successfully retrieved course materials")
            print(f"[DOWNLOAD_COURSE] Progress: {fetch_progress}")
            
            # Check for component errors
            components_with_errors = []
            if "modules_error" in course_materials:
                components_with_errors.append(f"modules ({course_materials.get('modules_error')})")
            if "files_error" in course_materials:
                components_with_errors.append(f"files ({course_materials.get('files_error')})")
            if "pages_error" in course_materials:
                # Only log non-404 errors for pages since some courses legitimately don't have pages
                if not str(course_materials.get('pages_error', '')).startswith("Pages feature not enabled"):
                    components_with_errors.append(f"pages ({course_materials.get('pages_error')})")
            
            if components_with_errors:
                print(f"[DOWNLOAD_COURSE] WARNING: Some components had errors: {', '.join(components_with_errors)}")
            
            # Log some basic stats about what we received
            modules_count = len(course_materials.get("modules", []))
            files_count = len(course_materials.get("files", []))
            pages_count = len(course_materials.get("pages", []))
            print(f"[DOWNLOAD_COURSE] Course contains: {modules_count} modules, {files_count} files, {pages_count} pages")
            
            # Initialize missing components to empty lists to avoid KeyError later
            for component in ["modules", "files", "pages", "assignments", "quizzes", "discussions"]:
                if component not in course_materials:
                    course_materials[component] = []
                elif course_materials[component] is None:
                    course_materials[component] = []
            
            fetch_progress = "materials_processed"
            print(f"[DOWNLOAD_COURSE] Progress: {fetch_progress}")
            
        except Exception as cm_error:
            print(f"[DOWNLOAD_COURSE] ERROR fetching course materials: {str(cm_error)}")
            print(f"[DOWNLOAD_COURSE] Progress when error occurred: {fetch_progress}")
            import traceback
            print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
            raise
        
        # Save course info
        print(f"[DOWNLOAD_COURSE] Saving course_info.json")
        try:
            # Add progress tracking
            save_progress = "starting"
            print(f"[DOWNLOAD_COURSE] Save progress: {save_progress}")
            
            # Create a more robust course_info object
            save_progress = "creating_json_object"
            course_info = {
                "course_id": course_id,
                "user_id": user_id,
                "timestamp": str(datetime.datetime.now()),
                "modules": course_materials.get("modules", []),
                "files": course_materials.get("files", []),
                "pages": course_materials.get("pages", []),
                "assignments": course_materials.get("assignments", []),
                "quizzes": course_materials.get("quizzes", []),
                "discussions": course_materials.get("discussions", [])
            }
            
            # Verify JSON serialization works
            save_progress = "testing_serialization"
            try:
                # Test serialization first to avoid partial file writes
                json_string = json.dumps(course_info)
                print(f"[DOWNLOAD_COURSE] JSON serialization successful, size: {len(json_string)} bytes")
            except Exception as json_error:
                print(f"[DOWNLOAD_COURSE] ERROR serializing course_info to JSON: {str(json_error)}")
                raise
            
            # Actually write to file
            save_progress = "writing_to_file"
            course_info_path = f"{course_dir}/course_info.json"
            with open(course_info_path, "w") as f:
                json.dump(course_info, f, indent=4)
            
            # Verify file was written
            save_progress = "verifying_file"
            if os.path.exists(course_info_path):
                file_size = os.path.getsize(course_info_path)
                print(f"[DOWNLOAD_COURSE] Successfully saved course_info.json, size: {file_size} bytes")
            else:
                print(f"[DOWNLOAD_COURSE] WARNING: course_info.json was not created at {course_info_path}")
                
        except Exception as save_error:
            print(f"[DOWNLOAD_COURSE] ERROR saving course_info.json: {str(save_error)}")
            print(f"[DOWNLOAD_COURSE] Save progress when error occurred: {save_progress}")
            import traceback
            print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
            raise
        
        # Create file list
        print(f"[DOWNLOAD_COURSE] Creating file list")
        try:
            # Add progress tracking
            files_progress = "starting"
            print(f"[DOWNLOAD_COURSE] Files progress: {files_progress}")
            
            file_list = []
            total_size = 0
            files_with_url = 0
            files_missing_url = 0
            
            # Make sure files exist in course_materials
            files_progress = "checking_files_exist"
            if "files" not in course_materials or course_materials["files"] is None:
                print(f"[DOWNLOAD_COURSE] No files found in course materials, initializing empty file list")
                course_materials["files"] = []
            
            # Debug output for files
            files_progress = "processing_files"
            print(f"[DOWNLOAD_COURSE] Processing {len(course_materials.get('files', []))} files")
            
            # Process files in batches to avoid timeouts
            batch_size = 50
            files_list = course_materials.get("files", [])
            total_files = len(files_list)
            
            for batch_start in range(0, total_files, batch_size):
                batch_end = min(batch_start + batch_size, total_files)
                print(f"[DOWNLOAD_COURSE] Processing files batch {batch_start}-{batch_end} of {total_files}")
                
                for i in range(batch_start, batch_end):
                    file_info = files_list[i]
                    
                    # Skip None or invalid entries
                    if file_info is None:
                        print(f"[DOWNLOAD_COURSE] WARNING: File {i} is None, skipping")
                        continue
                        
                    # Check if this is a valid file object with needed attributes
                    if not isinstance(file_info, dict):
                        print(f"[DOWNLOAD_COURSE] WARNING: File {i} is not a dict: {type(file_info)}, skipping")
                        continue
                    
                    has_url = "url" in file_info
                    if has_url:
                        files_with_url += 1
                    else:
                        files_missing_url += 1
                        print(f"[DOWNLOAD_COURSE] WARNING: File {i} missing URL: {file_info.get('display_name', 'unknown')}")
                        
                    # Log file info for debugging
                    if i < 5 or not has_url:  # Log first 5 files and any without URL
                        print(f"[DOWNLOAD_COURSE] File {i}: name='{file_info.get('display_name', 'unknown')}', "
                             f"has_url={has_url}, size={file_info.get('size', 0)}, "
                             f"content-type={file_info.get('content-type', 'unknown')}")
                    
                    # Only include files with URLs
                    if has_url:
                        try:
                            # Try to create a valid file record
                            display_name = file_info.get('display_name', f"file_{i}")
                            # Create a safe file path
                            file_path = f"{course_dir}/files/{display_name}"
                            file_size = int(file_info.get("size", 0))
                            total_size += file_size
                            
                            if file_size > 0:
                                FILE_SIZES.observe(file_size)
                            
                            file_list.append({
                                "name": display_name,
                                "path": file_path,
                                "type": file_info.get("content-type", ""),
                                "size": file_size,
                                "url": file_info.get("url", ""),
                                "id": file_info.get("id", "")
                            })
                        except Exception as file_error:
                            print(f"[DOWNLOAD_COURSE] ERROR processing file {i}: {str(file_error)}")
            
            # Handle empty file list
            files_progress = "finalizing_file_list"
            if len(file_list) == 0:
                print(f"[DOWNLOAD_COURSE] WARNING: No valid files found with URLs. Creating empty file_list.json")
            
            print(f"[DOWNLOAD_COURSE] File stats: {len(file_list)} total files, {files_with_url} with URL, {files_missing_url} missing URL")
            print(f"[DOWNLOAD_COURSE] Total file size: {total_size} bytes")
            
            # Create files directory even if there are no files
            files_progress = "creating_files_directory"
            os.makedirs(f"{course_dir}/files", exist_ok=True)
            
            # Save file list
            files_progress = "saving_file_list"
            print(f"[DOWNLOAD_COURSE] Saving file_list.json")
            file_list_path = f"{course_dir}/file_list.json"
            
            # Test JSON serialization before writing
            try:
                # Test serialization
                files_progress = "testing_file_list_json"
                json_string = json.dumps(file_list)
                print(f"[DOWNLOAD_COURSE] File list JSON serialization successful, size: {len(json_string)} bytes")
            except Exception as json_error:
                print(f"[DOWNLOAD_COURSE] ERROR serializing file_list to JSON: {str(json_error)}")
                # Try to create a simplified version
                file_list = [{"name": f.get("name", "unknown"), "id": f.get("id", "")} for f in file_list]
                print(f"[DOWNLOAD_COURSE] Created simplified file list with {len(file_list)} entries")
            
            # Write to file
            files_progress = "writing_file_list"
            with open(file_list_path, "w") as f:
                json.dump(file_list, f, indent=4)
            
            # Verify file was created
            files_progress = "verifying_file_list"
            if os.path.exists(file_list_path):
                file_size = os.path.getsize(file_list_path)
                print(f"[DOWNLOAD_COURSE] Successfully saved file_list.json, size: {file_size} bytes")
            else:
                print(f"[DOWNLOAD_COURSE] WARNING: file_list.json was not created")
            
            files_progress = "completed"
            
        except Exception as save_error:
            print(f"[DOWNLOAD_COURSE] ERROR processing file list: {str(save_error)}")
            print(f"[DOWNLOAD_COURSE] Files progress when error occurred: {files_progress}")
            import traceback
            print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
            
            # Try to save a minimal file list to avoid complete failure
            print(f"[DOWNLOAD_COURSE] Attempting to save minimal file_list.json")
            try:
                minimal_file_list = []
                file_list_path = f"{course_dir}/file_list.json"
                with open(file_list_path, "w") as f:
                    json.dump(minimal_file_list, f)
                print(f"[DOWNLOAD_COURSE] Saved minimal file_list.json as fallback")
            except Exception as minimal_error:
                print(f"[DOWNLOAD_COURSE] Could not save minimal file list: {str(minimal_error)}")
        
        # Add completion tracking
        completion_progress = "finalizing"
        print(f"[DOWNLOAD_COURSE] Finalizing course download, progress: {completion_progress}")
        
        # Record metrics
        print(f"[DOWNLOAD_COURSE] Incrementing download counter for course_id={course_id}")
        COURSE_DOWNLOADS.labels(course_id=str(course_id)).inc()
        
        # Create a status file to indicate completion
        completion_progress = "creating_status_file"
        status_file_path = f"{course_dir}/download_complete.txt"
        try:
            with open(status_file_path, "w") as f:
                f.write(f"Download completed: {datetime.datetime.now().isoformat()}")
            print(f"[DOWNLOAD_COURSE] Created status file: {status_file_path}")
        except Exception as status_error:
            print(f"[DOWNLOAD_COURSE] Warning: Could not create status file: {str(status_error)}")
        
        completion_progress = "completed"
        print(f"[DOWNLOAD_COURSE] Course {course_id} processed successfully")
        
        return {
            "message": f"Course {course_id} processed successfully",
            "user_id": user_id,  # Return the user_id that was used
            "course_dir": course_dir,  # Return the directory where the course was saved
            "status": "complete",
            "files_count": len(file_list),
            "modules_count": len(course_materials.get("modules", [])),
            "pages_count": len(course_materials.get("pages", []))
        }
    except PermissionError as pe:
        print(f"[DOWNLOAD_COURSE] PERMISSION ERROR processing course {course_id}: {str(pe)}")
        import traceback
        print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
        
        # Try to diagnose file system issues
        try:
            import subprocess
            print("[DOWNLOAD_COURSE] Checking directory permissions:")
            subprocess.run(["ls", "-la"], check=False)
            if os.path.exists("course_data"):
                subprocess.run(["ls", "-la", "course_data"], check=False)
            print("[DOWNLOAD_COURSE] Checking current user and group:")
            subprocess.run(["id"], check=False)
            print("[DOWNLOAD_COURSE] Checking disk space:")
            subprocess.run(["df", "-h"], check=False)
        except Exception as diagnosis_error:
            print(f"[DOWNLOAD_COURSE] Could not diagnose file system: {str(diagnosis_error)}")
        
        raise HTTPException(
            status_code=500, 
            detail="Permission denied while creating required directories. The application may not have write access to the file system. Please contact the administrator."
        )
    except json.JSONDecodeError as je:
        print(f"[DOWNLOAD_COURSE] JSON ERROR processing course {course_id}: {str(je)}")
        import traceback
        print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
        
        # Try to create minimal valid JSON files
        try:
            # Create directory structure if it doesn't exist
            os.makedirs(course_dir, exist_ok=True)
            os.makedirs(f"{course_dir}/files", exist_ok=True)
            
            # Save minimal course info
            with open(f"{course_dir}/course_info.json", "w") as f:
                json.dump({"course_id": course_id, "error": str(je)}, f)
                
            # Save minimal file list
            with open(f"{course_dir}/file_list.json", "w") as f:
                json.dump([], f)
                
            print(f"[DOWNLOAD_COURSE] Created minimal JSON files as fallback")
            
            return {
                "message": f"Course {course_id} processed with errors (JSON serialization failed)",
                "user_id": user_id,
                "course_dir": course_dir,
                "status": "error",
                "error": str(je)
            }
        except Exception as recovery_error:
            print(f"[DOWNLOAD_COURSE] Failed to create fallback files: {str(recovery_error)}")
            raise HTTPException(status_code=500, 
                              detail=f"JSON processing error: {str(je)}. Recovery attempt also failed.")
    except Exception as e:
        print(f"[DOWNLOAD_COURSE] FATAL ERROR processing course {course_id}: {str(e)}")
        import traceback
        print(f"[DOWNLOAD_COURSE] Traceback: {traceback.format_exc()}")
        
        # Try to respond with as much context as possible
        error_response = {
            "status": "error",
            "message": f"Error processing course {course_id}",
            "error_type": type(e).__name__,
            "error_details": str(e)
        }
        
        # Try to create a status file in the course directory if it exists
        if 'course_dir' in locals() and os.path.exists(course_dir):
            try:
                with open(f"{course_dir}/download_error.txt", "w") as f:
                    f.write(f"Download error at {datetime.datetime.now().isoformat()}: {str(e)}")
                error_response["course_dir"] = course_dir
            except:
                pass
        
        # Return a 500 with detailed error info
        raise HTTPException(status_code=500, detail=error_response)
    finally:
        # Time the entire operation
        if 'start_time' in locals():
            end_time = time.time()
            total_time = end_time - start_time
            print(f"[DOWNLOAD_COURSE] Total processing time: {total_time:.2f} seconds")
        
        # Decrement active requests
        ACTIVE_REQUESTS.dec()
        print(f"[DOWNLOAD_COURSE] Finished request for course_id={course_id}")

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
        
        # Always use the default collection
        # We don't create separate collections per course to avoid complexity
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
                
                # Determine the appropriate extension based on content type
                # For now, don't set a default extension - we'll determine it after looking at the content
                file_extension = ""  # Default to HTML
                
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
                
                # Clean the item name first
                item_name = clean_filename(item_name)
                
                # Check if the name already has a file extension
                name_parts = os.path.splitext(item_name)
                base_name = name_parts[0]
                name_ext = name_parts[1].lower()
                
                # Try to detect content type from file data (magic bytes)
                content_type = None
                is_pdf = False
                is_html = False
                is_image = False
                image_type = None
                
                try:
                    with open(temp_file_path, 'rb') as f:
                        first_bytes = f.read(50)  # Read more bytes to be sure
                        f.seek(0)  # Reset position
                        
                        # Check for PDF
                        if first_bytes.startswith(b'%PDF-'):
                            content_type = 'application/pdf'
                            is_pdf = True
                            print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as PDF based on magic bytes")
                        # Check for HTML
                        elif first_bytes.startswith(b'<!DOCTYPE') or b'<html' in first_bytes:
                            content_type = 'text/html'
                            is_html = True
                            print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as HTML based on content")
                        # Check for JPEG
                        elif first_bytes.startswith(b'\xff\xd8\xff'):
                            content_type = 'image/jpeg'
                            is_image = True
                            image_type = 'jpeg'
                            print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as JPEG image based on magic bytes")
                        # Check for PNG
                        elif first_bytes.startswith(b'\x89PNG'):
                            content_type = 'image/png'
                            is_image = True
                            image_type = 'png'
                            print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as PNG image based on magic bytes")
                        # Check for GIF
                        elif first_bytes.startswith(b'GIF87a') or first_bytes.startswith(b'GIF89a'):
                            content_type = 'image/gif'
                            is_image = True
                            image_type = 'gif'
                            print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as GIF image based on magic bytes")
                except Exception as e:
                    print(f"[UPLOAD_SELECTED_TO_RAG] Warning: Failed to detect content type from bytes: {str(e)}")
                    # Fallback to checking first bytes for HTML tags
                    with open(temp_file_path, 'rb') as f:
                        first_bytes = f.read(50)
                        is_html = b'<html' in first_bytes or b'<!DOCTYPE html' in first_bytes
                
                # Determine the correct extension based on content and original name
                if is_pdf:
                    # If it's actually a PDF, always use .pdf extension
                    if name_ext == '.pdf':
                        # Already has correct extension
                        filename = item_name
                    else:
                        # Add PDF extension
                        filename = f"{base_name}.pdf"
                    print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as PDF, using filename: {filename}")
                elif is_image:
                    # For image files, ensure they have the right extension
                    correct_ext = f".{image_type}"
                    
                    if name_ext.lower() == correct_ext:
                        # Already has the correct extension
                        filename = item_name
                    else:
                        # Add correct image extension
                        filename = f"{base_name}{correct_ext}"
                    
                    print(f"[UPLOAD_SELECTED_TO_RAG] Content identified as {image_type.upper()} image, using filename: {filename}")
                    
                    # For image files, use the image captioning capabilities
                    # No need for text descriptor files as the VLM model will generate captions
                    try:
                        # Upload image with image captioning enabled
                        print(f"[UPLOAD_SELECTED_TO_RAG] Uploading image with captioning enabled: {filename}")
                        await upload_to_rag(temp_file_path, filename, collection_name)
                        
                        # Skip the regular upload below since we handled it specially
                        success_count += 1
                        print(f"[UPLOAD_SELECTED_TO_RAG] Successfully processed image file {i+1}")
                        
                        # Clean up temp file
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        
                        # Continue to next file, skipping the regular upload
                        continue
                    except Exception as img_error:
                        print(f"[UPLOAD_SELECTED_TO_RAG] ERROR processing image file: {str(img_error)}")
                        # Continue with regular upload as fallback
                elif is_html:
                    # If content is HTML, use .html extension, but avoid double extensions
                    if name_ext == '.html':
                        # Already has .html extension
                        filename = item_name
                    elif name_ext and '.html' in name_ext:
                        # Has something like .pdf.html - remove the .html part
                        clean_name = item_name.lower().replace('.html', '')
                        filename = f"{clean_name}"
                    else:
                        # No html in extension, add .html
                        filename = f"{item_name}.html"
                    print(f"[UPLOAD_SELECTED_TO_RAG] Content appears to be HTML, using filename: {filename}")
                else:
                    # Not HTML content, use original name with extension
                    if name_ext:
                        # Already has an extension
                        filename = item_name
                    else:
                        # No extension, use the one we determined
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
    # Check if the course_data directory exists and is writable
    base_dir = "course_data"
    directory_exists = os.path.exists(base_dir)
    directory_writable = False
    
    if directory_exists:
        try:
            test_file_path = os.path.join(base_dir, "write_test.txt")
            with open(test_file_path, "w") as f:
                f.write("write test")
            os.remove(test_file_path)
            directory_writable = True
        except Exception as e:
            directory_writable = False
            print(f"[HEALTH] Warning: course_data directory is not writable: {str(e)}")
    
    status = "ok" if directory_exists and directory_writable else "degraded"
    
    return {
        "status": status,
        "service": "course_data_manager",
        "timestamp": str(datetime.datetime.now()),
        "directory_status": {
            "course_data_exists": directory_exists,
            "course_data_writable": directory_writable
        }
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

# Function to ensure course_data directory exists and is writable
def ensure_data_directories():
    """Ensure that the course_data directory exists and is writable"""
    base_dir = "course_data"
    print(f"[STARTUP] Checking if base directory exists: {base_dir}")
    
    # Check if the directory exists
    if not os.path.exists(base_dir):
        try:
            print(f"[STARTUP] Creating base directory: {base_dir}")
            os.mkdir(base_dir)
            print(f"[STARTUP] Successfully created base directory: {base_dir}")
        except Exception as e:
            print(f"[STARTUP] ERROR creating base directory: {str(e)}")
            print("[STARTUP] *** WARNING: Course data directory does not exist and cannot be created! ***")
            print("[STARTUP] *** The application may not function correctly. ***")
            return False
    
    # Check if the directory is writable
    test_file_path = os.path.join(base_dir, "write_test.txt")
    try:
        with open(test_file_path, "w") as f:
            f.write("write test")
        os.remove(test_file_path)
        print(f"[STARTUP] Base directory {base_dir} is writable")
        return True
    except Exception as e:
        print(f"[STARTUP] ERROR: Base directory {base_dir} is not writable: {str(e)}")
        print("[STARTUP] *** WARNING: Course data directory is not writable! ***")
        print("[STARTUP] *** The application may not function correctly. ***")
        
        # Try to diagnose permission issues
        try:
            import subprocess
            print("[STARTUP] Checking directory permissions:")
            subprocess.run(["ls", "-la", base_dir], check=False)
            print("[STARTUP] Checking current user and group:")
            subprocess.run(["id"], check=False)
        except Exception as diagnosis_error:
            print(f"[STARTUP] Could not diagnose permissions: {str(diagnosis_error)}")
        
        return False

if __name__ == "__main__":
    # Print configuration information
    print("=" * 80)
    print("Course Manager API - Starting Server")
    print(f"- RAG Server URL: {RAG_SERVER_URL}")
    print(f"- Ingestion Server URL: {INGESTION_SERVER_URL}")
    print(f"- Image Captioning: Enabled")
    print(f"- VLM Caption Endpoint: {os.environ.get('VLM_CAPTION_ENDPOINT')}")
    print("=" * 80)
    
    # Check if the course_data directory exists and is writable
    data_dir_ok = ensure_data_directories()
    if not data_dir_ok:
        print("[STARTUP] WARNING: Data directory issues might prevent course downloads")
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=True)