# DroneSim
---

# Drone Simulator 🚁

A fully-fledged drone simulator backed by Django Rest Framework and an accompanying administrative website.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
  - [API](#api)
  - [Admin Website](#admin-website)
- [Features](#features)
- [Contribution](#contribution)
- [License](#license)

## Overview

This project aims to simulate drone movements and behavior in a controlled environment. The backend API is developed using Django Rest Framework, providing real-time data of the drone, such as coordinates, altitude, and speed. The administrative website is designed to monitor and manage drone simulations.
There exists also an OpenAPI-based API documentation using redoc or swaggerUI (both available according to your preferences).

## Installation
IMPORTANT: The following installation instruction is outdated, as the project now uses docker-compose and pipenv

1. **Clone the repository**
   ```bash
   git clone https://github.com/rmuellerb/DroneSim.git
   ```

2. **Navigate to the project directory**
   ```bash
   cd DroneSim
   ```
3. **Configure according to your requirements**
   ```bash
   vim env.prod
   # or for the development environment:
   vim env.dev
   ```

4. **Run the production server using docker-compose (using nginx, WSGI and postgres)**
   ```bash
   docker compose -f docker-compose.prod.yaml up --build -d
   ```

5. **(optional) Run the development server using docker-compose (using the internal django web server and postgres)**
   ```bash
   docker compose -f docker-compose.dev.yaml up --build -d
   ```

6. **Create admin user after db was initially created within the container**
   ```bash
   docker ps # find the container ID
   docker exec -it <container id> python manage.py createsuperuser
   ```
7. **Create new certificates**
    It is important that you create new certificates for your production server, as the ones provided are just for testing purposes.

## Usage

### API

- Access the drone simulation API at:
  ```
  http://<configured IP>/api/
  ```

- [API Documentation](http://<configured IP>/redoc) provides a comprehensive guide on the available endpoints. Alternatively you can use swaggerUI which is available at .../swagger/

### Admin Website

- Access the administrative website at:
  ```
  http://<configured IP>/admin/
  ```

- Use the credentials created before to login

## Features

- **Pre-computed Drone Simulation**: Simulate a drone's movement in a pre-computed manner, from taking off to empty battery.
  
- **Django Admin Integration**: Monitor and manage drone simulations through the administrative website.

- **API**: Retrieve and manage drone data using the Django Rest Framework-backed API.

- **SSL/TLS**: if you want to use SSL/TLS, create your certifciate and configure them in the nginx/ directory. Remember to put the certificates in the directory and tell Dockerfile to copy them. Self-signed certificates may introduce issues when interacting with the API if not configured properly, so consider using a service such as letsencrypt.

## Contribution

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

Distributed under the MIT License. See `LICENSE` for more information.

---
