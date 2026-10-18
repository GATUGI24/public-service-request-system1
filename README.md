project Title

Public Service Request System (Mini eCitizen)

 Overview:

This project implements a web-based platform for reporting and managing public service issues such as broken streetlights, water supply problems, and garbage collection. The system serves two user roles — citizens and administrators — and provides end-to-end functionality from issue submission to resolution.

Core Functionality

Citizen registration and login, multi-field request submission with image upload, unique ticket generation, public ticket tracking, admin dashboard with status updates and comments, and basic analytics on open vs. resolved cases.

Technologies Used: Python, Flask, SQLite, SQLAlchemy, Flask-Login, Werkzeug (password hashing and file handling), HTML5, Jinja2, Bootstrap 5.

Design Approach:The application follows an MVC-like structure with SQLAlchemy models, route handlers in `app.py`, and Jinja2 templates for presentation. The UI is responsive and uses role-based redirects to keep citizen and admin experiences separate.
