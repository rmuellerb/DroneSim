FROM python:3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy project
COPY . /app/
