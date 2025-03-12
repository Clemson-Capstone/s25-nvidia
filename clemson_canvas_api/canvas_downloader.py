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
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=ssl_context) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Failed to download file: {response_text}")
            
            with open(temp_file_path, "wb") as f:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
    
    return temp_file_path

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
            
            # Get quiz questions even if we don't have a submission
            if not quiz_questions or not quiz_questions.get('quiz_questions'):
                try:
                    # CRITICAL CHANGE: Try getting questions with answers using the special endpoint
                    questions_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions?quiz_submission_attempt=1&quiz_submission_id={submission_id}" if submission_id else f"https://clemson.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
                    async with session.get(questions_url, headers=headers) as questions_response:
                        if questions_response.status == 200:
                            quiz_questions = await questions_response.json()
                            print(f"Quiz questions found: {len(quiz_questions.get('quiz_questions', [])) if quiz_questions and 'quiz_questions' in quiz_questions else 'None'}")
                except Exception as e:
                    print(f"Error fetching quiz questions: {str(e)}")
            
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
    api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/files/{file_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"File info error: {error_text}")
                raise HTTPException(status_code=response.status, detail=f"Failed to get file info: {error_text}")
            
            file_info = await response.json()
            download_url = file_info.get('url')
            
            if not download_url:
                raise HTTPException(status_code=404, detail="File download URL not found")
            
            # Now download the actual file
            async with session.get(download_url, headers=headers) as file_response:
                if file_response.status != 200:
                    error_text = await file_response.text()
                    print(f"File download error: {error_text}")
                    raise HTTPException(status_code=file_response.status, detail=f"Failed to download file: {error_text}")
                
                content_type = file_response.headers.get("Content-Type", "application/octet-stream")
                
                # If no filename provided, use the one from the file info
                if not filename:
                    filename = file_info.get("display_name", "canvas_file")
                
                # Return the file content
                file_content = await file_response.read()
                return Response(
                    content=file_content,
                    media_type=content_type,
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
    try:
        # Handle different content types using appropriate API endpoints
        item_type_lower = item_type.lower()
        
        if item_type_lower == 'assignment':
            return await download_assignment(course_id, item_id, token, filename)
            
        elif item_type_lower in ['page', 'wiki_page']:
            return await download_page_content(course_id, item_id, token, filename)
            
        elif item_type_lower in ['quiz', 'quizzes/quiz']:
            return await download_quiz(course_id, item_id, token, filename)
            
        elif item_type_lower == 'file':
            return await download_file_content(course_id, item_id, token, filename)
            
        elif item_type_lower in ['discussion_topic', 'discussion']:
            return await download_discussion(course_id, item_id, token, filename)
            
        elif item_type_lower == 'externalurl':
            # For external URLs, we need to get the URL from the module item first
            api_url = f"https://clemson.instructure.com/api/v1/courses/{course_id}/modules/items/{item_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        item_data = await response.json()
                        if 'external_url' in item_data:
                            return await download_external_url(item_data['external_url'], token, filename)
            
            # If we couldn't get the URL, use a placeholder
            return await download_external_url("https://clemson.instructure.com", token, filename)
            
        else:
            # For unsupported types, return a generic message
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
                </div>
            </body>
            </html>
            """
            
            if not filename:
                filename = "unsupported_content.html"
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
    
    except Exception as e:
        # Log the full exception for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))