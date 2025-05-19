# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the frontend app and its requirements
COPY ./frontend_streamlit/requirements.txt /app/frontend_requirements.txt
COPY ./frontend_streamlit/app.py /app/app.py

# Copy the backend module and its requirements
# The backend code is in the 'run_restaurant_finder' directory at the root
# The Docker build context will be the root of the repository.
# So, when this Dockerfile (located in frontend_streamlit) is built,
# the paths for COPY should be relative to the build context (repository root).
COPY ./run_restaurant_finder /app/run_restaurant_finder
COPY ./run_restaurant_finder/requirements.txt /app/backend_requirements.txt

# Install frontend dependencies
RUN pip install --no-cache-dir -r frontend_requirements.txt

# Install backend dependencies
RUN pip install --no-cache-dir -r backend_requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV PYTHONUNBUFFERED 1

# Run app.py when the container launches
CMD ["streamlit", "run", "app.py"]
