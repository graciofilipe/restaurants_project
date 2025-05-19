# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# --- Copy Simulation Code ---
# into the container under the working directory.
COPY restaurant_finder/ ./restaurant_finder/
COPY streamlit_app.py .

# --- Install Dependencies ---
# Copy the full requirements file for the simulation
COPY requirements.txt .

# Install Python dependencies for Flask AND the simulation
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir --upgrade pip
# Flask is no longer needed
RUN pip install --no-cache-dir -r requirements.txt 

RUN apt update
#RUN apt install -y graphviz


# Optional: Set PYTHONPATH if your simulation code uses relative imports across modules
ENV PYTHONPATH=/app

# Run streamlit_app.py when the container launches
# Use shell form to allow $PORT substitution
ENTRYPOINT streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0