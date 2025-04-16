import os
import json
import aiohttp
import ssl
import certifi
from fastapi import HTTPException
from fastapi.responses import Response
import traceback

"""
Canvas Downloader Module

This module provides functions for downloading different types of content from Canvas LMS.
It's designed to be used with the Course Data Manager API.
"""

async def download_file_async(url, token, temp_file_path):
    """Download a file from Canvas asynchronously"""
    print(f"[DOWNLOAD_FILE] Starting download from URL: {url}")
    print(f"[DOWNLOAD_FILE] Target path: {temp_file_path}")
    print(f"[DOWNLOAD_FILE] Token length: {len(token)}")
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    print(f"[DOWNLOAD_FILE] Headers: {headers}")
    
    try:
        total_size = 0
        start_time = None
        
        async with aiohttp.ClientSession() as session:
            # Log request start time
            import time
            start_time = time.time()
            print(f"[DOWNLOAD_FILE] Starting request at {start_time}")
            
            # First try to make a HEAD request to get content-length and other metadata
            try:
                async with session.head(url, headers=headers, ssl=ssl_context) as head_response:
                    print(f"[DOWNLOAD_FILE] HEAD response status: {head_response.status}")
                    print(f"[DOWNLOAD_FILE] HEAD response headers: {head_response.headers}")
                    content_length = head_response.headers.get('Content-Length')
                    if content_length:
                        print(f"[DOWNLOAD_FILE] Content length: {content_length} bytes")
                    content_type = head_response.headers.get('Content-Type')
                    if content_type:
                        print(f"[DOWNLOAD_FILE] Content type: {content_type}")
            except Exception as head_error:
                print(f"[DOWNLOAD_FILE] HEAD request failed (non-fatal): {str(head_error)}")
            
            # Now make the actual GET request to download the file
            print(f"[DOWNLOAD_FILE] Sending GET request to download file")
            
            try:
                async with session.get(url, headers=headers, ssl=ssl_context) as response:
                    print(f"[DOWNLOAD_FILE] GET response status: {response.status}")
                    print(f"[DOWNLOAD_FILE] GET response headers: {response.headers}")
                    
                    # Check if the response is successful
                    if response.status != 200:
                        response_text = await response.text()
                        print(f"[DOWNLOAD_FILE] ERROR: Failed to download file. Status: {response.status}, Response: {response_text}")
                        raise Exception(f"Failed to download file: {response_text}")
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                    
                    # Download the file in chunks
                    print(f"[DOWNLOAD_FILE] Writing file to: {temp_file_path}")
                    with open(temp_file_path, "wb") as f:
                        chunk_count = 0
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            chunk_size = len(chunk)
                            total_size += chunk_size
                            chunk_count += 1
                            f.write(chunk)
                            
                            # Log progress for every 10 chunks or large files
                            if chunk_count % 10 == 0 or chunk_size > 1000000:
                                print(f"[DOWNLOAD_FILE] Downloaded {total_size} bytes so far ({chunk_count} chunks)")
                
                # Log successful download completion and file size
                end_time = time.time()
                duration = end_time - start_time
                print(f"[DOWNLOAD_FILE] Download completed in {duration:.2f} seconds")
                print(f"[DOWNLOAD_FILE] Total file size: {total_size} bytes")
                
                # Verify file exists and has content
                if os.path.exists(temp_file_path):
                    file_size = os.path.getsize(temp_file_path)
                    print(f"[DOWNLOAD_FILE] Verified file on disk: {temp_file_path}, size: {file_size} bytes")
                    
                    if file_size == 0:
                        print(f"[DOWNLOAD_FILE] WARNING: Downloaded file is empty (0 bytes)")
                else:
                    print(f"[DOWNLOAD_FILE] ERROR: File does not exist after download: {temp_file_path}")
                    raise Exception("File does not exist after download")
            
            except Exception as e:
                print(f"[DOWNLOAD_FILE] ERROR during download: {str(e)}")
                import traceback
                print(f"[DOWNLOAD_FILE] Traceback: {traceback.format_exc()}")
                raise
        
        return temp_file_path
    
    except Exception as e:
        print(f"[DOWNLOAD_FILE] FATAL ERROR: {str(e)}")
        import traceback
        print(f"[DOWNLOAD_FILE] Traceback: {traceback.format_exc()}")
        raise

async def download_page_async(url, token, temp_file_path):
    """Download a page content from Canvas asynchronously"""
    # Extract page URL and convert it to API URL
    # Example: https://clemson.instructure.com/courses/123/pages/page-name -> /api/v1/courses/123/pages/page-name
    
    # Parse URL to extract course_id and page_name
    parts = url.split('/')
    course_index = parts.index('courses')
    course_id = parts[course_index + 1]
    page_index = parts.index('pages')
    page_name = parts[page_index + 1]
    
    # Build API URL
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/pages/{page_name}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Failed to download page: {response_text}")
            
            page_data = await response.json()
            
            # Write page content to a markdown file
            with open(temp_file_path, "w") as f:
                f.write(f"# {page_data.get('title', 'Untitled Page')}\n\n")
                f.write(page_data.get('body', ''))
    
    return temp_file_path

async def download_assignment_async(url, token, temp_file_path):
    """Download an assignment content from Canvas asynchronously"""
    # Parse URL to extract course_id and assignment_id
    parts = url.split('/')
    course_index = parts.index('courses')
    course_id = parts[course_index + 1]
    assignment_index = parts.index('assignments')
    assignment_id = parts[assignment_index + 1]
    
    # Build API URL
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/assignments/{assignment_id}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Failed to download assignment: {response_text}")
            
            assignment_data = await response.json()
            
            # Write assignment content to a markdown file
            with open(temp_file_path, "w") as f:
                f.write(f"# {assignment_data.get('name', 'Untitled Assignment')}\n\n")
                f.write(f"**Points:** {assignment_data.get('points_possible', 'N/A')}\n\n")
                f.write(f"**Due Date:** {assignment_data.get('due_at', 'No due date')}\n\n")
                f.write(assignment_data.get('description', ''))
    
    return temp_file_path

async def download_module_item_async(url, token, item_type, temp_file_path):
    """Download a module item based on its type"""
    if item_type.lower() == 'file':
        return await download_file_async(url, token, temp_file_path)
    elif item_type.lower() == 'page':
        return await download_page_async(url, token, temp_file_path)
    elif item_type.lower() == 'assignment':
        return await download_assignment_async(url, token, temp_file_path)
    else:
        # For other types, try to fetch the content as HTML
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"Failed to download content: {response_text}")
                
                content = await response.text()
                
                # Write content to a file
                with open(temp_file_path, "w") as f:
                    f.write(content)
        
        return temp_file_path

async def download_assignment(course_id: str, assignment_id: str, token: str, filename: str = None):
    """Download an assignment from Canvas using the assignment ID"""
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/assignments/{assignment_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Assignment download error: {error_text}")
                raise HTTPException(status_code=response.status, detail=f"Failed to get assignment: {error_text}")
            
            data = await response.json()
            
            # Format the assignment as HTML
            html_content = f"""
            <html>
            <head>
                <title>{data.get('name', 'Assignment')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1 {{ color: #2d3b45; }}
                    .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .description {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>{data.get('name', 'Assignment')}</h1>
                <div class="details">
                    <p><strong>Points:</strong> {data.get('points_possible', 'N/A')}</p>
                    <p><strong>Due Date:</strong> {data.get('due_at', 'No due date')}</p>
                </div>
                <div class="description">
                    {data.get('description', 'No description provided.')}
                </div>
            </body>
            </html>
            """
            
            if not filename:
                filename = f"{data.get('name', 'assignment').replace(' ', '_')}.html"
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

async def download_quiz(course_id: str, quiz_id: str, token: str, filename: str = None, include_results: bool = True):
    """Download a quiz from Canvas using the quiz ID, optionally including submission results and answers"""
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Quiz download error: {error_text}")
                raise HTTPException(status_code=response.status, detail=f"Failed to get quiz: {error_text}")
            
            quiz_data = await response.json()
            
            # Collect quiz submission and question data
            submission_data = None
            quiz_questions = None
            submission_id = None
            
            if include_results:
                try:
                    # First check if the user has any submissions for this quiz
                    submissions_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions"
                    async with session.get(submissions_url, headers=headers) as submissions_response:
                        if submissions_response.status == 200:
                            submissions = await submissions_response.json()
                            print(f"Submissions response: {submissions}")
                            
                            if submissions.get('quiz_submissions') and len(submissions['quiz_submissions']) > 0:
                                # Sort submissions by attempt number (descending) to get the most recent one
                                sorted_submissions = sorted(
                                    submissions['quiz_submissions'], 
                                    key=lambda x: x.get('attempt', 0), 
                                    reverse=True
                                )
                                submission = sorted_submissions[0]
                                submission_id = submission['id']
                                print(f"Found submission ID: {submission_id}, attempt: {submission.get('attempt')}")
                                
                                # Use the submission ID to get questions with student answers
                                submission_questions_url = f"https://clemson.instructure.com/api/v1/quiz_submissions/{submission_id}/questions"
                                async with session.get(submission_questions_url, headers=headers) as questions_response:
                                    if questions_response.status == 200:
                                        questions_data = await questions_response.json()
                                        print(f"Direct submission questions response: {questions_data is not None}")
                                        if questions_data and 'quiz_submission_questions' in questions_data:
                                            quiz_questions = {'quiz_questions': questions_data['quiz_submission_questions']}
                
                except Exception as e:
                    print(f"Error fetching quiz submission: {str(e)}")
                    traceback.print_exc()
                    # Continue without submission data if there's an error
            # Start building the HTML content for the quiz
            html_content = f"""
            <html>
            <head>
                <title>{quiz_data.get('title', 'Quiz')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1, h2, h3 {{ color: #2d3b45; }}
                    .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .description {{ margin-top: 20px; margin-bottom: 30px; }}
                    .questions {{ margin-top: 30px; }}
                    .question {{ margin-bottom: 25px; border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; }}
                    .question-text {{ font-weight: bold; margin-bottom: 10px; }}
                    .answers {{ margin-left: 20px; margin-top: 10px; }}
                    .answer {{ padding: 5px; margin-bottom: 5px; }}
                </style>
            </head>
            <body>
                <h1>{quiz_data.get('title', 'Quiz')}</h1>
                <div class="details">
                    <p><strong>Due Date:</strong> {quiz_data.get('due_at', 'No due date')}</p>
                    <p><strong>Time Limit:</strong> {quiz_data.get('time_limit', 'None')} minutes</p>
                    <p><strong>Quiz Type:</strong> {quiz_data.get('quiz_type', 'Unknown')}</p>
                    <p><strong>Allowed Attempts:</strong> {quiz_data.get('allowed_attempts', '1')}</p>
                </div>
            """
            
            if quiz_data.get('description'):
                html_content += f"""
                <div class="description">
                    <h2>Description</h2>
                    {quiz_data.get('description', '')}
                </div>
                """
            
            # Add questions with answers if available
            if quiz_questions and ('quiz_questions' in quiz_questions or 'quiz_submission_questions' in quiz_questions):
                html_content += '<h2>Questions</h2>'
                
                question_list = quiz_questions.get('quiz_questions', quiz_questions.get('quiz_submission_questions', []))
                
                for question in question_list:
                    question_text = question.get('question_text', 'No question text')
                    question_type = question.get('question_type', 'unknown')
                    
                    html_content += f"""
                    <div class="question">
                        <div class="question-text">{question_text}</div>
                    """
                    
                    # Add the answer options
                    if 'answers' in question:
                        html_content += '<div class="answers">'
                        
                        for answer in question['answers']:
                            answer_text = answer.get('text', '') or answer.get('html', '')
                            html_content += f"""
                            <div class="answer">
                                {answer_text}
                            </div>
                            """
                        
                        html_content += '</div>'  # Close answers div
                    
                    # Handle essay/text questions
                    elif question_type in ['essay_question', 'text_only_question', 'short_answer_question']:
                        html_content += f"""
                        <div class="answers">
                            <div class="answer">
                                <em>[Text entry field]</em>
                            </div>
                        </div>
                        """
                    
                    html_content += '</div>'  # Close question div
            
            # Close HTML document
            html_content += """
            </body>
            </html>
            """
            
            if not filename:
                filename = f"{quiz_data.get('title', 'quiz').replace(' ', '_')}.html"
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )


async def download_page_content(course_id: str, page_id: str, token: str, filename: str = None):
    """Download a page from Canvas using the page ID"""
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/pages/{page_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Page download error: {error_text}")
                raise HTTPException(status_code=response.status, detail=f"Failed to get page: {error_text}")
            
            data = await response.json()
            
            # Format the page as HTML
            html_content = f"""
            <html>
            <head>
                <title>{data.get('title', 'Page')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1 {{ color: #2d3b45; }}
                </style>
            </head>
            <body>
                <h1>{data.get('title', 'Page')}</h1>
                <div>
                    {data.get('body', 'No content provided.')}
                </div>
            </body>
            </html>
            """
            
            if not filename:
                filename = f"{data.get('title', 'page').replace(' ', '_')}.html"
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

async def download_discussion(course_id: str, discussion_id: str, token: str, filename: str = None):
    """Download a discussion from Canvas using the discussion ID"""
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/discussion_topics/{discussion_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Discussion download error: {error_text}")
                raise HTTPException(status_code=response.status, detail=f"Failed to get discussion: {error_text}")
            
            data = await response.json()
            
            # Format the discussion as HTML
            html_content = f"""
            <html>
            <head>
                <title>{data.get('title', 'Discussion')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1 {{ color: #2d3b45; }}
                    .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .message {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>{data.get('title', 'Discussion')}</h1>
                <div class="details">
                    <p><strong>Posted at:</strong> {data.get('posted_at', 'Unknown date')}</p>
                </div>
                <div class="message">
                    {data.get('message', 'No content provided.')}
                </div>
            </body>
            </html>
            """
            
            if not filename:
                filename = f"{data.get('title', 'discussion').replace(' ', '_')}.html"
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

async def download_file_content(course_id: str, file_id: str, token: str, filename: str = None):
    """Download a file from Canvas using the file ID"""
    print(f"[DOWNLOAD_FILE_CONTENT] Starting download for course_id={course_id}, file_id={file_id}")
    print(f"[DOWNLOAD_FILE_CONTENT] Requested filename: {filename}")
    print(f"[DOWNLOAD_FILE_CONTENT] Token length: {len(token)}")
    
    try:
        import time
        start_time = time.time()
        print(f"[DOWNLOAD_FILE_CONTENT] Started at: {start_time}")
        
        # Use URL-encoded token to avoid any special character issues
        token = token.strip()
        api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/files/{file_id}"
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[DOWNLOAD_FILE_CONTENT] Using API URL: {api_url}")
        print(f"[DOWNLOAD_FILE_CONTENT] Headers: {headers}")
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with aiohttp.ClientSession() as session:
            # First request to get file info
            print(f"[DOWNLOAD_FILE_CONTENT] Making initial request to get file info")
            try:
                async with session.get(api_url, headers=headers, ssl=ssl_context) as response:
                    print(f"[DOWNLOAD_FILE_CONTENT] File info response status: {response.status}")
                    print(f"[DOWNLOAD_FILE_CONTENT] File info response headers: {response.headers}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[DOWNLOAD_FILE_CONTENT] ERROR: File info request failed: {error_text}")
                        raise HTTPException(status_code=response.status, detail=f"Failed to get file info: {error_text}")
                    
                    file_info = await response.json()
                    print(f"[DOWNLOAD_FILE_CONTENT] Successfully retrieved file info: {file_info.get('display_name')}")
                    print(f"[DOWNLOAD_FILE_CONTENT] File info: {file_info}")
            except Exception as file_info_error:
                print(f"[DOWNLOAD_FILE_CONTENT] EXCEPTION during file info request: {str(file_info_error)}")
                import traceback
                print(f"[DOWNLOAD_FILE_CONTENT] File info traceback: {traceback.format_exc()}")
                raise
                
                # Try multiple download methods in order of preference
                
                # Determine proper mime type and filename upfront
                original_filename = file_info.get("display_name", "file")
                content_type = file_info.get("content-type", "application/octet-stream")
                file_size = file_info.get("size", 0)
                file_modified = file_info.get("updated_at", "unknown")
                
                print(f"[DOWNLOAD_FILE_CONTENT] Original file metadata: name={original_filename}, type={content_type}, size={file_size}, modified={file_modified}")
                
                # Make sure we don't add .html extension when we already have a content type
                if not filename:
                    filename = original_filename
                    print(f"[DOWNLOAD_FILE_CONTENT] Using original filename: {filename}")
                else:
                    print(f"[DOWNLOAD_FILE_CONTENT] Using provided filename: {filename}")
                
                # Check file properties
                print(f"[DOWNLOAD_FILE_CONTENT] File URL available: {'url' in file_info}")
                if 'url' in file_info:
                    print(f"[DOWNLOAD_FILE_CONTENT] File URL: {file_info.get('url')}")
                
                # Method 1: Try direct Canvas download endpoint using the API v1 URL (most reliable)
                print(f"[DOWNLOAD_FILE_CONTENT] === METHOD 1: Direct API Download ===")
                try:
                    # This is the most reliable way to download from Canvas - using the API
                    direct_url = f"https://clemson.instructure.com/api/v1/files/{file_id}/download"
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 1 URL: {direct_url}")
                    
                    # Ensure proper auth header format based on Canvas API docs
                    api_headers = {
                        "Authorization": f"Bearer {token}",
                        "Accept": "*/*"
                    }
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 1 headers: {api_headers}")
                    
                    method1_start = time.time()
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 1 request starting at: {method1_start}")
                    
                    async with session.get(direct_url, headers=api_headers, ssl=ssl_context, allow_redirects=True) as file_response:
                        method1_status = file_response.status
                        method1_headers = file_response.headers
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 1 response status: {method1_status}")
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 1 response headers: {method1_headers}")
                        
                        if method1_status == 200:
                            response_content_type = method1_headers.get("Content-Type", content_type)
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 1 content type: {response_content_type}")
                            
                            try:
                                file_content = await file_response.read()
                                content_length = len(file_content)
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 1 SUCCESS: Downloaded {content_length} bytes")
                                
                                # Check if content seems valid
                                if content_length == 0:
                                    print(f"[DOWNLOAD_FILE_CONTENT] WARNING: Method 1 returned empty content (0 bytes)")
                                    raise Exception("Empty file content")
                                
                                if content_length < 100:
                                    # For small content, print it to help debugging
                                    try:
                                        text_preview = file_content.decode('utf-8', errors='replace')[:100]
                                        print(f"[DOWNLOAD_FILE_CONTENT] Content preview: {text_preview}")
                                    except:
                                        print(f"[DOWNLOAD_FILE_CONTENT] Content is binary, no preview available")
                                
                                # Check if expected file size matches
                                if file_size > 0 and content_length != file_size:
                                    print(f"[DOWNLOAD_FILE_CONTENT] WARNING: Downloaded size ({content_length}) doesn't match expected size ({file_size})")
                                
                                method1_end = time.time()
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 1 completed in {method1_end - method1_start:.2f} seconds")
                                
                                return Response(
                                    content=file_content,
                                    media_type=response_content_type,
                                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                                )
                            except Exception as read_error:
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 1 read error: {str(read_error)}")
                                raise
                        else:
                            error_text = await file_response.text()
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 1 failed with status {method1_status}: {error_text}")
                            
                            # If we get a 401 or 403, there might be authentication issues
                            if method1_status in [401, 403]:
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 1 failed with auth error: {method1_status}")
                                
                            # If we get a 404, the file might not exist
                            if method1_status == 404:
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 1 failed with 404 - file not found")
                except Exception as e1:
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 1 exception: {str(e1)}")
                    import traceback
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 1 traceback: {traceback.format_exc()}")
                
                # Method 2: Try using the URL from the file info
                print(f"[DOWNLOAD_FILE_CONTENT] === METHOD 2: Using file_info URL ===")
                download_url = file_info.get('url')
                if download_url:
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 URL: {download_url}")
                    try:
                        # According to Canvas docs, the file.url might be a pre-signed URL that doesn't need auth
                        # So we'll try without auth headers first
                        method2_start = time.time()
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 2 request starting at: {method2_start}")
                        
                        async with session.get(download_url, ssl=ssl_context, allow_redirects=True) as file_response:
                            method2_status = file_response.status
                            method2_headers = file_response.headers
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 2 response status: {method2_status}")
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 2 response headers: {method2_headers}")
                            
                            if method2_status == 200:
                                response_content_type = method2_headers.get("Content-Type", "application/octet-stream")
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 2 content type: {response_content_type}")
                                
                                try:
                                    file_content = await file_response.read()
                                    content_length = len(file_content)
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 SUCCESS: Downloaded {content_length} bytes")
                                    
                                    # Check if content seems valid
                                    if content_length == 0:
                                        print(f"[DOWNLOAD_FILE_CONTENT] WARNING: Method 2 returned empty content (0 bytes)")
                                        raise Exception("Empty file content")
                                    
                                    if content_length < 100:
                                        # For small content, print it to help debugging
                                        try:
                                            text_preview = file_content.decode('utf-8', errors='replace')[:100]
                                            print(f"[DOWNLOAD_FILE_CONTENT] Content preview: {text_preview}")
                                        except:
                                            print(f"[DOWNLOAD_FILE_CONTENT] Content is binary, no preview available")
                                    
                                    # Check if expected file size matches
                                    if file_size > 0 and content_length != file_size:
                                        print(f"[DOWNLOAD_FILE_CONTENT] WARNING: Downloaded size ({content_length}) doesn't match expected size ({file_size})")
                                    
                                    method2_end = time.time()
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 completed in {method2_end - method2_start:.2f} seconds")
                                    
                                    if not filename:
                                        filename = file_info.get("display_name", "canvas_file")
                                    
                                    return Response(
                                        content=file_content,
                                        media_type=response_content_type,
                                        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                                    )
                                except Exception as read_error:
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 read error: {str(read_error)}")
                                    raise
                            else:
                                error_text = await file_response.text()
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 2 failed with status {method2_status}: {error_text}")
                        
                        # If the first attempt failed, try again with authorization headers
                        if method2_status != 200:
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 2 retrying with auth headers")
                            api_headers = {
                                "Authorization": f"Bearer {token}",
                                "Accept": "*/*"
                            }
                            async with session.get(download_url, headers=api_headers, ssl=ssl_context, allow_redirects=True) as auth_response:
                                method2_auth_status = auth_response.status
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 2 auth response status: {method2_auth_status}")
                                
                                if method2_auth_status == 200:
                                    content_type = auth_response.headers.get("Content-Type", "application/octet-stream")
                                    file_content = await auth_response.read()
                                    content_length = len(file_content)
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 with auth SUCCESS: Downloaded {content_length} bytes")
                                    
                                    return Response(
                                        content=file_content,
                                        media_type=content_type,
                                        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                                    )
                                else:
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 with auth failed: {method2_auth_status}")
                        
                    except Exception as e2:
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 2 exception: {str(e2)}")
                        import traceback
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 2 traceback: {traceback.format_exc()}")
                else:
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 2 skipped: No URL in file_info")
                
                # Method 3: Try global files endpoint with the specific download parameter
                try:
                    global_url = f"https://clemson.instructure.com/api/v1/files/{file_id}?include[]=avatar"
                    print(f"Attempting Method 3: API files endpoint with additional parameters: {global_url}")
                    
                    # Ensure proper auth header format based on Canvas API docs
                    api_headers = {
                        "Authorization": f"Bearer {token}",
                        "Accept": "*/*"
                    }
                    
                    async with session.get(global_url, headers=api_headers, ssl=ssl_context, allow_redirects=True) as file_response:
                        if file_response.status == 200:
                            content_type = file_response.headers.get("Content-Type", "application/octet-stream")
                            file_content = await file_response.read()
                            print(f"Method 3 SUCCESS: Downloaded {len(file_content)} bytes")
                            
                            if not filename:
                                filename = file_info.get("display_name", "canvas_file")
                            
                            return Response(
                                content=file_content,
                                media_type=content_type,
                                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                            )
                        else:
                            print(f"Method 3 failed with status {file_response.status}")
                except Exception as e3:
                    print(f"Method 3 exception: {str(e3)}")
                
                # Try the traditional download URL without API prefix
                try:
                    direct_download_url = f"https://clemson.instructure.com/courses/{course_id}/files/{file_id}/download?download_frd=1&verifier={file_info.get('uuid', '')}"
                    print(f"Attempting Method 4: Direct download URL with verifier: {direct_download_url}")
                    
                    async with session.get(direct_download_url, headers=headers, ssl=ssl_context, allow_redirects=True) as file_response:
                        if file_response.status == 200:
                            content_type = file_response.headers.get("Content-Type", "application/octet-stream")
                            file_content = await file_response.read()
                            print(f"Method 4 SUCCESS: Downloaded {len(file_content)} bytes")
                            
                            if not filename:
                                filename = file_info.get("display_name", "canvas_file")
                            
                            return Response(
                                content=file_content,
                                media_type=content_type,
                                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                            )
                        else:
                            print(f"Method 4 failed with status {file_response.status}")
                except Exception as e4:
                    print(f"Method 4 exception: {str(e4)}")
                
                # Method 5: Try the Canvas Files API endpoint with a different token format
                print(f"[DOWNLOAD_FILE_CONTENT] === METHOD 5: Files API with enhanced preview URL ===")
                try:
                    api_method_url = f"https://clemson.instructure.com/api/v1/files/{file_id}?include[]=enhanced_preview_url"
                    cookie_headers = {
                        "Cookie": f"_csrf_token={token}; canvas_session={token}",
                        "Accept": "*/*"
                    }
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 URL: {api_method_url}")
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 cookie headers: {cookie_headers}")
                    
                    method5_start = time.time()
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 request starting at: {method5_start}")
                    
                    async with session.get(api_method_url, headers=cookie_headers, ssl=ssl_context) as api_response:
                        method5_status = api_response.status
                        method5_headers = api_response.headers
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 5 response status: {method5_status}")
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 5 response headers: {method5_headers}")
                        
                        if method5_status == 200:
                            try:
                                api_data = await api_response.json()
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 API data keys: {list(api_data.keys() if isinstance(api_data, dict) else [])}")
                                
                                if isinstance(api_data, dict) and "enhanced_preview_url" in api_data:
                                    preview_url = api_data["enhanced_preview_url"]
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 found enhanced_preview_url: {preview_url}")
                                    
                                    # Attempt to download using the preview URL
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 attempting preview download")
                                    try:
                                        async with session.get(preview_url, headers=cookie_headers, ssl=ssl_context) as preview_response:
                                            preview_status = preview_response.status
                                            preview_headers = preview_response.headers
                                            print(f"[DOWNLOAD_FILE_CONTENT] Method 5 preview response status: {preview_status}")
                                            print(f"[DOWNLOAD_FILE_CONTENT] Method 5 preview headers: {preview_headers}")
                                            
                                            if preview_status == 200:
                                                response_content_type = preview_headers.get("Content-Type", "application/octet-stream")
                                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 preview content type: {response_content_type}")
                                                
                                                file_content = await preview_response.read()
                                                content_length = len(file_content)
                                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 SUCCESS: Downloaded {content_length} bytes")
                                                
                                                # Check if content seems valid
                                                if content_length == 0:
                                                    print(f"[DOWNLOAD_FILE_CONTENT] WARNING: Method 5 returned empty content (0 bytes)")
                                                    raise Exception("Empty file content")
                                                
                                                method5_end = time.time()
                                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 completed in {method5_end - method5_start:.2f} seconds")
                                                
                                                if not filename:
                                                    filename = file_info.get("display_name", "canvas_file")
                                                
                                                return Response(
                                                    content=file_content,
                                                    media_type=response_content_type,
                                                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                                                )
                                            else:
                                                error_text = await preview_response.text()
                                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 preview download failed with status {preview_status}: {error_text}")
                                    except Exception as preview_error:
                                        print(f"[DOWNLOAD_FILE_CONTENT] Method 5 preview download error: {str(preview_error)}")
                                        raise
                                else:
                                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 did not find enhanced_preview_url in response")
                            except Exception as json_error:
                                print(f"[DOWNLOAD_FILE_CONTENT] Method 5 JSON parsing error: {str(json_error)}")
                                raise
                        else:
                            error_text = await api_response.text()
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 5 failed with status {method5_status}: {error_text}")
                except Exception as e5:
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 exception: {str(e5)}")
                    import traceback
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 5 traceback: {traceback.format_exc()}")
                
                # Method 6: Try another API endpoint format as last resort
                print(f"[DOWNLOAD_FILE_CONTENT] === METHOD 6: Alternative API endpoint format ===")
                try:
                    alt_url = f"https://clemson.instructure.com/api/v1/files/{file_id}?include[]=user&include[]=usage_rights"
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 6 URL: {alt_url}")
                    
                    method6_start = time.time()
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 6 request starting at: {method6_start}")
                    
                    async with session.get(alt_url, headers=headers, ssl=ssl_context) as alt_response:
                        method6_status = alt_response.status
                        print(f"[DOWNLOAD_FILE_CONTENT] Method 6 response status: {method6_status}")
                        
                        if method6_status == 200:
                            alt_data = await alt_response.json()
                            print(f"[DOWNLOAD_FILE_CONTENT] Method 6 received JSON data with keys: {list(alt_data.keys() if isinstance(alt_data, dict) else [])}")
                            
                            # Look for any download URLs in the response
                            if isinstance(alt_data, dict):
                                for key in ['url', 'download_url', 'preview_url']:
                                    if key in alt_data and alt_data[key]:
                                        download_url = alt_data[key]
                                        print(f"[DOWNLOAD_FILE_CONTENT] Method 6 found download URL in '{key}': {download_url}")
                                        
                                        # Try to download with this URL
                                        async with session.get(download_url, ssl=ssl_context, allow_redirects=True) as download_response:
                                            if download_response.status == 200:
                                                file_content = await download_response.read()
                                                print(f"[DOWNLOAD_FILE_CONTENT] Method 6 SUCCESS: Downloaded {len(file_content)} bytes")
                                                
                                                if not filename:
                                                    filename = file_info.get("display_name", "canvas_file")
                                                
                                                return Response(
                                                    content=file_content,
                                                    media_type=download_response.headers.get("Content-Type", "application/octet-stream"),
                                                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                                                )
                except Exception as e6:
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 6 exception: {str(e6)}")
                    import traceback
                    print(f"[DOWNLOAD_FILE_CONTENT] Method 6 traceback: {traceback.format_exc()}")
                
                # All methods failed, create a fallback HTML but with more context
                print(f"[DOWNLOAD_FILE_CONTENT] All download methods failed, creating fallback HTML")
                
                # Get additional file details for better context
                file_type = file_info.get('content-type', 'Unknown')
                file_size = file_info.get('size', 'Unknown')
                file_created = file_info.get('created_at', 'Unknown')
                file_updated = file_info.get('updated_at', 'Unknown')
                file_display_name = file_info.get('display_name', 'File')
                file_uuid = file_info.get('uuid', 'Unknown')
                file_mime_class = file_info.get('mime_class', 'Unknown')
                
                print(f"[DOWNLOAD_FILE_CONTENT] Creating fallback HTML with file details:")
                print(f"[DOWNLOAD_FILE_CONTENT] - Type: {file_type}")
                print(f"[DOWNLOAD_FILE_CONTENT] - Size: {file_size}")
                print(f"[DOWNLOAD_FILE_CONTENT] - Created: {file_created}")
                print(f"[DOWNLOAD_FILE_CONTENT] - Updated: {file_updated}")
                print(f"[DOWNLOAD_FILE_CONTENT] - Display Name: {file_display_name}")
                print(f"[DOWNLOAD_FILE_CONTENT] - UUID: {file_uuid}")
                print(f"[DOWNLOAD_FILE_CONTENT] - MIME Class: {file_mime_class}")
                
                # Additional debugging info
                available_urls = []
                if 'url' in file_info:
                    available_urls.append(("File info URL", file_info.get('url')))
                available_urls.append(("API download endpoint", f"https://clemson.instructure.com/api/v1/files/{file_id}/download"))
                available_urls.append(("Direct Canvas URL", f"https://clemson.instructure.com/courses/{course_id}/files/{file_id}"))
                available_urls.append(("Download URL with verifier", f"https://clemson.instructure.com/courses/{course_id}/files/{file_id}/download?download_frd=1&verifier={file_uuid}"))
                
                # Create a richer HTML fallback with file details and Canvas URI
                html_content = f"""
                <html>
                <head>
                    <title>{file_display_name}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                        h1 {{ color: #2d3b45; }}
                        .container {{ margin: 20px auto; max-width: 800px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                        .metadata {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                        .actions {{ margin-top: 20px; text-align: center; }}
                        .actions a {{ display: inline-block; padding: 10px 20px; background-color: #0374B5; color: white; 
                                     text-decoration: none; border-radius: 5px; margin: 0 10px; }}
                        .actions a:hover {{ background-color: #0262A0; }}
                        .note {{ font-style: italic; margin-top: 30px; color: #666; }}
                        pre {{ background: #f8f8f8; padding: 10px; overflow-x: auto; }}
                        .error {{ background: #fff0f0; color: #d32f2f; padding: 10px; border-radius: 5px; margin-top: 20px; }}
                        .timestamp {{ color: #666; font-size: 0.8em; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>{file_display_name}</h1>
                        
                        <div class="metadata">
                            <h3>File Information</h3>
                            <p><strong>File Type:</strong> {file_type}</p>
                            <p><strong>Size:</strong> {file_size} bytes</p>
                            <p><strong>Created:</strong> {file_created}</p>
                            <p><strong>Last Updated:</strong> {file_updated}</p>
                            <p><strong>File ID:</strong> {file_id}</p>
                            <p><strong>Course ID:</strong> {course_id}</p>
                            <p><strong>MIME Class:</strong> {file_mime_class}</p>
                            <p><strong>UUID:</strong> {file_uuid}</p>
                        </div>
                        
                        <div class="actions">
                            <a href="https://clemson.instructure.com/courses/{course_id}/files/{file_id}" target="_blank">
                                View in Canvas
                            </a>
                            <a href="https://clemson.instructure.com/courses/{course_id}/files/{file_id}/download?download_frd=1" target="_blank">
                                Download File
                            </a>
                        </div>
                        
                        <p class="note">Note: You may need to be logged into Canvas to access this file. This file could not be automatically downloaded.</p>
                        
                        <div class="error">
                            <h3>Error Notice</h3>
                            <p>The system was unable to directly download this file for the knowledge base. This may be due to permission settings, file type restrictions, or other Canvas API limitations.</p>
                        </div>
                        
                        <div>
                            <h3>Debug Information</h3>
                            <p>The following download URLs were attempted:</p>
                            <pre>"""
                
                # Add all attempted URLs to the debug info
                for i, (url_name, url) in enumerate(available_urls):
                    html_content += f"{i+1}. {url_name}: {url}\n"
                
                html_content += f"""</pre>
                        </div>
                        
                        <p class="timestamp">Attempted download: {datetime.datetime.now().isoformat()}</p>
                    </div>
                </body>
                </html>
                """
                
                if not filename:
                    filename = f"{file_display_name.replace(' ', '_')}_unavailable.html"
                    print(f"[DOWNLOAD_FILE_CONTENT] Generated filename: {filename}")
                
                print(f"[DOWNLOAD_FILE_CONTENT] Returning fallback HTML response, length: {len(html_content)}")
                return Response(
                    content=html_content,
                    media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )
                
    except Exception as e:
        print(f"[DOWNLOAD_FILE_CONTENT] FATAL EXCEPTION: {str(e)}")
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[DOWNLOAD_FILE_CONTENT] Error traceback: {error_traceback}")
        
        # Get as much info as possible about the file
        file_info_str = "Unknown"
        try:
            if 'file_info' in locals() and file_info:
                # Try to extract useful info even if we can't access the whole object
                info_parts = []
                for k in ['display_name', 'content-type', 'size', 'id', 'uuid']:
                    if k in file_info:
                        info_parts.append(f"{k}={file_info.get(k)}")
                file_info_str = ", ".join(info_parts)
        except:
            pass
        
        print(f"[DOWNLOAD_FILE_CONTENT] File info: {file_info_str}")
        
        # Log all attempted download methods
        print(f"[DOWNLOAD_FILE_CONTENT] Attempted download methods:")
        download_methods = {
            "Method 1": f"API download endpoint (api/v1/files/{file_id}/download)",
            "Method 2": "file_info URL",
            "Method 3": f"Global files endpoint (api/v1/files/{file_id}?include[]=avatar)",
            "Method 4": f"Direct download URL with verifier",
            "Method 5": "Enhanced preview URL",
            "Method 6": "Alternative API endpoint"
        }
        for method, description in download_methods.items():
            print(f"[DOWNLOAD_FILE_CONTENT] - {method}: {description}")
        
        # Get error type and message
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[DOWNLOAD_FILE_CONTENT] Error type: {error_type}")
        print(f"[DOWNLOAD_FILE_CONTENT] Error message: {error_msg}")
        
        # Create a graceful error HTML with comprehensive debugging information
        html_content = f"""
        <html>
        <head>
            <title>File Download Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1 {{ color: #d32f2f; }}
                h2 {{ color: #2d3b45; margin-top: 30px; }}
                .container {{ margin: 20px auto; max-width: 800px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .error {{ color: #d32f2f; font-family: monospace; white-space: pre-wrap; text-align: left; 
                         padding: 10px; background: #f5f5f5; overflow-x: auto; }}
                .actions {{ margin-top: 20px; text-align: center; }}
                .actions a {{ display: inline-block; padding: 10px 20px; background-color: #0374B5; color: white; 
                             text-decoration: none; border-radius: 5px; margin: 0 10px; }}
                .actions a:hover {{ background-color: #0262A0; }}
                .metadata {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .note {{ font-style: italic; margin-top: 30px; color: #666; }}
                .timestamp {{ color: #666; font-size: 0.8em; margin-top: 20px; }}
                details {{ margin: 10px 0; }}
                summary {{ cursor: pointer; padding: 5px; background: #f0f0f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>File Download Error</h1>
                <p>There was an error downloading this file from Canvas. The system could not retrieve the file content directly.</p>
                
                <div class="actions">
                    <a href="https://clemson.instructure.com/courses/{course_id}/files/{file_id}" target="_blank">
                        Access File in Canvas
                    </a>
                    <a href="https://clemson.instructure.com/courses/{course_id}/files/{file_id}/download?download_frd=1" target="_blank">
                        Direct Download Link
                    </a>
                </div>
                
                <div class="metadata">
                    <h2>File Information</h2>
                    <p><strong>Course ID:</strong> {course_id}</p>
                    <p><strong>File ID:</strong> {file_id}</p>
                    <p><strong>File Info:</strong> {file_info_str}</p>
                    <p><strong>Requested Filename:</strong> {filename or "Not specified"}</p>
                </div>
                
                <details>
                    <summary>Error details (click to expand)</summary>
                    <h3>Error Type: {error_type}</h3>
                    <div class="error">{error_msg}</div>
                </details>
                
                <details>
                    <summary>Attempted Download Methods</summary>
                    <ul>
                        <li><strong>Method 1:</strong> API download endpoint (api/v1/files/{file_id}/download)</li>
                        <li><strong>Method 2:</strong> Pre-signed URL from file info object</li>
                        <li><strong>Method 3:</strong> Global files endpoint with avatar parameter</li>
                        <li><strong>Method 4:</strong> Direct download URL with verifier token</li>
                        <li><strong>Method 5:</strong> Enhanced preview URL from files API</li>
                        <li><strong>Method 6:</strong> Alternative API endpoint format</li>
                    </ul>
                </details>
                
                <p class="note">This file was being downloaded for the knowledge base integration but encountered an error. You can try accessing it directly in Canvas using the links above.</p>
                
                <p class="timestamp">Error occurred at: {datetime.datetime.now().isoformat()}</p>
            </div>
        </body>
        </html>
        """
        
        if not filename:
            filename = f"error_file_{file_id}.html"
        
        print(f"[DOWNLOAD_FILE_CONTENT] Returning error HTML response, length: {len(html_content)}")
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

async def download_external_url(url: str, token: str, filename: str = None):
    """Create a page that redirects to an external URL"""
    html_content = f"""
    <html>
    <head>
        <title>External URL Content</title>
        <meta http-equiv="refresh" content="3;url={url}" />
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; text-align: center; }}
            h1 {{ color: #2d3b45; }}
            .container {{ margin-top: 50px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>External URL Content</h1>
            <p>This content is available at: <a href="{url}">{url}</a></p>
            <p>You will be redirected to this URL in 3 seconds.</p>
        </div>
    </body>
    </html>
    """
    
    if not filename:
        filename = "external_content.html"
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

async def get_course_item_content(course_id: str, item_id: str, item_type: str, token: str, filename: str = None):
    """
    Retrieve content for a specific course item directly using its ID and type.
    This function is specifically designed for items from course_info.json.
    
    Parameters:
    - course_id: The Canvas course ID
    - item_id: The content ID (assignment ID, quiz ID, etc.)
    - item_type: The type of content (Assignment, Quiz, Page, etc.)
    - token: Canvas API token for authentication
    - filename: Optional filename for the downloaded content
    
    Returns:
    - Response with the content and appropriate headers
    """
    print(f"[GET_COURSE_ITEM] Starting request for course_id={course_id}, item_id={item_id}, item_type={item_type}")
    print(f"[GET_COURSE_ITEM] Filename: {filename}, Token length: {len(token)}")
    
    try:
        # Handle different content types using appropriate API endpoints
        item_type_lower = item_type.lower()
        print(f"[GET_COURSE_ITEM] Processing item_type: {item_type_lower}")
        
        if item_type_lower == 'assignment':
            print(f"[GET_COURSE_ITEM] Calling download_assignment for item_id={item_id}")
            try:
                response = await download_assignment(course_id, item_id, token, filename)
                print(f"[GET_COURSE_ITEM] Assignment download successful")
                return response
            except Exception as assignment_error:
                print(f"[GET_COURSE_ITEM] ERROR downloading assignment: {str(assignment_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] Assignment traceback: {traceback.format_exc()}")
                raise
            
        elif item_type_lower in ['page', 'wiki_page']:
            print(f"[GET_COURSE_ITEM] Calling download_page_content for item_id={item_id}")
            try:
                response = await download_page_content(course_id, item_id, token, filename)
                print(f"[GET_COURSE_ITEM] Page download successful")
                return response
            except Exception as page_error:
                print(f"[GET_COURSE_ITEM] ERROR downloading page: {str(page_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] Page traceback: {traceback.format_exc()}")
                raise
            
        elif item_type_lower in ['quiz', 'quizzes/quiz']:
            print(f"[GET_COURSE_ITEM] Calling download_quiz for item_id={item_id}")
            try:
                response = await download_quiz(course_id, item_id, token, filename)
                print(f"[GET_COURSE_ITEM] Quiz download successful")
                return response
            except Exception as quiz_error:
                print(f"[GET_COURSE_ITEM] ERROR downloading quiz: {str(quiz_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] Quiz traceback: {traceback.format_exc()}")
                raise
            
        elif item_type_lower == 'file':
            print(f"[GET_COURSE_ITEM] Calling download_file_content for item_id={item_id}")
            try:
                response = await download_file_content(course_id, item_id, token, filename)
                print(f"[GET_COURSE_ITEM] File download successful")
                return response
            except Exception as file_error:
                print(f"[GET_COURSE_ITEM] ERROR downloading file: {str(file_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] File traceback: {traceback.format_exc()}")
                raise
            
        elif item_type_lower in ['discussion_topic', 'discussion']:
            print(f"[GET_COURSE_ITEM] Calling download_discussion for item_id={item_id}")
            try:
                response = await download_discussion(course_id, item_id, token, filename)
                print(f"[GET_COURSE_ITEM] Discussion download successful")
                return response
            except Exception as discussion_error:
                print(f"[GET_COURSE_ITEM] ERROR downloading discussion: {str(discussion_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] Discussion traceback: {traceback.format_exc()}")
                raise
            
        elif item_type_lower == 'externalurl':
            print(f"[GET_COURSE_ITEM] Processing external URL for item_id={item_id}")
            try:
                # For external URLs, we need to get the URL from the module item first
                api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/modules/items/{item_id}"
                headers = {"Authorization": f"Bearer {token}"}
                print(f"[GET_COURSE_ITEM] Fetching external URL from: {api_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, headers=headers) as response:
                        print(f"[GET_COURSE_ITEM] External URL response status: {response.status}")
                        
                        if response.status == 200:
                            item_data = await response.json()
                            print(f"[GET_COURSE_ITEM] External URL item data: {item_data}")
                            
                            if 'external_url' in item_data:
                                external_url = item_data['external_url']
                                print(f"[GET_COURSE_ITEM] Found external URL: {external_url}")
                                return await download_external_url(external_url, token, filename)
                            else:
                                print(f"[GET_COURSE_ITEM] No external_url found in item data")
                        else:
                            error_text = await response.text()
                            print(f"[GET_COURSE_ITEM] Failed to get module item: {error_text}")
                
                # If we couldn't get the URL, use a placeholder
                print(f"[GET_COURSE_ITEM] Using placeholder URL")
                return await download_external_url("https://clemson.instructure.com", token, filename)
            except Exception as external_url_error:
                print(f"[GET_COURSE_ITEM] ERROR processing external URL: {str(external_url_error)}")
                import traceback
                print(f"[GET_COURSE_ITEM] External URL traceback: {traceback.format_exc()}")
                raise
            
        else:
            # For unsupported types, return a generic message
            print(f"[GET_COURSE_ITEM] Unsupported item type: {item_type_lower}")
            html_content = f"""
            <html>
            <head>
                <title>Unsupported Content Type</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; text-align: center; }}
                    h1 {{ color: #2d3b45; }}
                    .container {{ margin-top: 50px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Unsupported Content Type</h1>
                    <p>The content type '{item_type}' is not currently supported for direct download.</p>
                    <p>You may need to access this content directly in Canvas.</p>
                    <p>Item ID: {item_id}</p>
                    <p>Course ID: {course_id}</p>
                </div>
            </body>
            </html>
            """
            
            if not filename:
                filename = f"unsupported_content_{item_type_lower}.html"
            
            print(f"[GET_COURSE_ITEM] Returning unsupported content response with filename: {filename}")
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
    
    except Exception as e:
        # Log the full exception for debugging
        print(f"[GET_COURSE_ITEM] FATAL ERROR: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"[GET_COURSE_ITEM] Traceback: {traceback_str}")
        
        # Create an error response HTML
        error_html = f"""
        <html>
        <head>
            <title>Error Retrieving Content</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1 {{ color: #d32f2f; }}
                .error {{ background-color: #ffebee; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; font-family: monospace; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>Error Retrieving Content</h1>
            <p>There was an error retrieving the requested content from Canvas.</p>
            
            <div class="error">
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
            
            <div class="details">
                <p><strong>Details:</strong></p>
                <p>Course ID: {course_id}</p>
                <p>Item ID: {item_id}</p>
                <p>Item Type: {item_type}</p>
                <p>Timestamp: {datetime.datetime.now().isoformat()}</p>
            </div>
        </body>
        </html>
        """
        
        # Return the error HTML response
        return Response(
            content=error_html,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="error_report.html"'}
        )