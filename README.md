# Spring 2025 NVIDIA Capstone Project

## Project Description
This project is building upon the work of the fall 2024 capstone project. The goal of this project is to
create a Virtual Teaching Assistant (VTA) that integrates with canvas and can be used as an example
of what NVIDIA's microservices can do.

## Getting Started
To get started, you will need to have Docker and Docker Compose installed on your machine. Once you have these installed, you must creare an .env.local file with `NVIDIA_API_KEY="nvapi-..."` in it.

### Running everything at once
If you want to run the entire project, the RAG, frontend and everything, then please run `make dev`.

The RAG Playground will be available at [http://localhost:8090](http://localhost:8090).

The frontend will be available at [http://localhost:3000](http://localhost:3000) (unless you have that port in use).

### RAG playground
After you have set that up, you can run following command from the root of the project to start RAG part project:
`make setup`. This will run `make login`, `make deploy`, and `make status` in order.

After that, you can navigate to [http://localhost:8090](http://localhost:8090) to see the Nvidia RAG Playground.

Run `make clean` to stop the containers and remove the volumes.

### Frontend
If this is your first time running the frontend, you can run `make frontend-install` to install the dependencies. After that, you can run `make frontend-dev` to start the frontend in development mode. This will start the server on port 3000 and will automatically reload the page when you make changes to the code. 

If you want to build the frontend for production, you can run `make frontend-build` to build the frontend. This will create a `dist` folder in the `frontend` directory with the built files. You can then run `make frontend-start` to start the frontend in production mode. This will start the server on port 3000 and will serve the files from the `dist` folder.

## Repository Structure
#### `frontend`
Contains the frontend code for the VTA. This is a NextJS 15 app, using TailwindCSS. 

#### `foundational-rag`
Contains the code for NVIDIA's foundational RAG.

#### `clemson-canvas-grab`
Taken from the Fall 2024 capstone project, this folder is a fork of [canvas-grab](https://github.com/skyzh/canvas_grab) that 
has been modified to grab canvas data for clemson students by the Fall 2024 capstone team
