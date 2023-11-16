FROM python:3.11.4-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set work directory
ENV HOME=/app
RUN mkdir $HOME
RUN mkdir $HOME/staticfiles
WORKDIR $HOME

# Install system dependencies
RUN apt-get update && apt-get install -y netcat

# Install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy project
COPY . /app/

ENTRYPOINT ["/app/entrypoint.sh"]
