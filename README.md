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
   git clone https://github.com/your-github-username/DroneSim.git
   ```

2. **Navigate to the project directory**
   ```bash
   cd DroneSim
   ```

3. **Switch to Pipenv**
   ```bash
   pipenv shell
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the server using docker-compose**
   ```bash
   docker-compose up --build
   ```

6. **Create admin user after db was initially created**
   ```bash
   python3 manage.py createsuperuser
   ```

## Usage

### API

- Access the drone simulation API at:
  ```
  http://localhost/api/
  ```

- [API Documentation](http://localhost/redoc) provides a comprehensive guide on the available endpoints. Alternatively you can use swaggerUI which is available at .../swagger/

### Admin Website

- Access the administrative website at:
  ```
  http://localhost/admin/
  ```

- Use the credentials created before to login

## Features

- **Pre-computed Drone Simulation**: Simulate a drone's movement in a pre-computed manner, from taking off to empty battery.
  
- **Django Admin Integration**: Monitor and manage drone simulations through the administrative website.

- **API**: Retrieve and manage drone data using the Django Rest Framework-backed API.

## Contribution

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

Distributed under the MIT License. See `LICENSE` for more information.

---
