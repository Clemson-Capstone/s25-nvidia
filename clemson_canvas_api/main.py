from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import os
import json
from typing import Dict, List, Union, Optional
import requests
import tempfile
import shutil
import aiohttp
import ssl
import certifi
import asyncio
import io

# Import the module downloader functionality
from canvas_downloader import (
    download_file_async, 
    download_page_async, 
    download_assignment_async, 
    download_module_item_async,
    get_course_item_content
)

app = FastAPI(title="Course Data Manager API")

# Configure CORS - more permissive to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the RAG server URL
RAG_SERVER_URL = "http://localhost:8081"

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

async def upload_to_rag(file_path, file_name):
    """Upload a file to the RAG server"""
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f)}
        response = requests.post(f"{RAG_SERVER_URL}/documents", files=files)
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload to RAG: {response.text}")
        
        return response.json()

@app.post("/get_courses", response_model=Dict[str, str])
async def get_courses(request: TokenRequest):
    """
    Gets a list of all the courses the user is enrolled in with their ids and names using just the token
    """
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
    
    try:
        client = CanvasClient(token)
        # Use the user_id from request if provided, otherwise use the one from the Canvas client
        user_id = request.user_id or str(client.user_id)
        
        # Create directory structure
        course_dir = f"course_data/{user_id}/{course_id}"
        os.makedirs(course_dir, exist_ok=True)
        
        # Get course info
        course_materials = client.get_course_materials(course_id)
        
        # Save course info
        with open(f"{course_dir}/course_info.json", "w") as f:
            json.dump(course_materials, f, indent=4)
        
        # Create file list
        file_list = []
        for file_info in course_materials.get("files", []):
            if "url" in file_info:
                file_path = f"{course_dir}/files/{file_info.get('display_name', 'unknown')}"
                file_list.append({
                    "name": file_info.get("display_name", ""),
                    "path": file_path,
                    "type": file_info.get("content-type", ""),
                    "size": file_info.get("size", 0),
                    "url": file_info.get("url", "")
                })
        
        # Save file list
        with open(f"{course_dir}/file_list.json", "w") as f:
            json.dump(file_list, f, indent=4)
            
        return {
            "message": f"Course {course_id} processed successfully",
            "user_id": user_id  # Return the user_id that was used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                return [{"name": file.get("display_name", "")} for file in files]
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

@app.post("/download_and_upload_to_rag")
async def download_and_upload_to_rag(request: DownloadAndUploadRequest):
    """
    Download content from Canvas and upload it to the RAG server
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    if not request.token:
        raise HTTPException(status_code=400, detail="Token is required")
    
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
            
            # Upload to RAG
            rag_response = await upload_to_rag(temp_file_path, file_name)
            
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

# Add endpoint for getting course item content directly from course_info.json
@app.get("/get_course_item")
async def get_course_item(course_id: str, content_id: str, item_type: str, token: str, filename: str = None):
    """
    Get content for a specific course item by ID and type
    """
    print(f"get_course_item called with: course_id={course_id}, content_id={content_id}, item_type={item_type}")
    return await get_course_item_content(course_id, content_id, item_type, token, filename)

@app.get("/download_module_item")
async def download_module_item(course_id: str, module_id: str, item_id: str, token: str):
    """
    Download a specific module item from Canvas
    This endpoint handles downloads from course_info.json items
    """
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
        
@app.get("/user_info")
async def get_user_info(token: str):
    """
    Get information about the current user
    """
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

@app.get("/")
async def index():
    return {"message": "Course Data Manager API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=True)