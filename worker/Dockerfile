# Use an official Python runtime as a parent imageFROM python:3.8-slim
FROM python:3-alpine

# Set the working directory in the container
WORKDIR /usr/src/worker

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME Worker

# Run worker.py when the container launches
CMD ["python", "worker.py"]