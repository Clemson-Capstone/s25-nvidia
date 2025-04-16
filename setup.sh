#!/bin/bash
 
 set -e  # Exit on any error
 
 # Create a virtual environment in .venv folder
 python3 -m venv .venv
 
 # Activate the virtual environment
 source .venv/bin/activate
 
 # Upgrade pip 
 pip install --upgrade pip
 
 # Install dependencies from your project
 pip install -r nvidia-rag-2.0/requirements.txt
 pip install -r course_manager_api/requirements.txt
 pip install -r nvidia-rag-2.0/src/ingestor_server/requirements.txt
 
 # Install shared/ as an editable package if it exists
 if [ -d "shared" ]; then
     pip install -e shared/
 fi
 
 echo "Python environment setup complete!"