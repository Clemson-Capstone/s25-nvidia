if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=True)
    
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import Dict, List, Union, Optional
import requests

app = FastAPI(title="Course Data Manager API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
    return {"message": "You're on the course data manager!"}