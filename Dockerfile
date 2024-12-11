FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME World
RUN python manage.py collectstatic --noinput
# Run manage.py when the container launches
CMD ["uvicorn", "legal_assistant.asgi:application", "--host", "0.0.0.0", "--port","8000"]
