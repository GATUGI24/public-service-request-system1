# Public Service Request System (Mini eCitizen)

A Flask + SQLite web app for citizens to report public issues and admins to manage them.

## Features
- Citizen registration & login (hashed passwords)
- Submit service requests (category, location, description, image, priority)
- Unique ticket number (PSR-YYYYMMDDHHMMSS)
- Public status tracking (no login needed)
- Admin dashboard with analytics (open vs resolved, by category)
- Status workflow: Pending → In Progress → Resolved
- Admin comments on each request

## Setup
```bash
pip install -r requirements.txt
python app.py