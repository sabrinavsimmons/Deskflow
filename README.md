# DeskFlow — Self-Hosted IT Ticketing System

A lightweight IT help desk ticketing system built with Python, Flask, and SQLite.
Deployed on a Ubuntu Server 24.04 VM running in a Proxmox homelab environment.

## Features

**Tickets**
- Create, view, edit, and delete support tickets
- Priority levels: low, medium, high, critical
- Status tracking: open, in progress, resolved, closed
- Activity thread with timestamped notes per ticket
- Note author auto-populated from logged-in user

**Dashboard**
- Live stats: open, in progress, resolved, and critical counts
- Filter tickets by status
- Search by title, category, or assignee
- Export all tickets to CSV

**Authentication & User Management**
- Login/logout with session management
- Passwords hashed with Werkzeug
- Change password from the UI
- Add and delete users from the UI

## Tech Stack

- **Backend:** Python 3.12, Flask 3.1, SQLite
- **Frontend:** Jinja2 templates, HTML/CSS
- **Server:** Gunicorn 25.3
- **Process management:** systemd
- **Infrastructure:** Ubuntu Server 24.04 VM on Proxmox VE

## Project Structure
```

ticketing-app/
├── app.py                  # Flask routes and application logic
├── database.py             # SQLite database setup and connection
├── tickets.db              # SQLite database file
├── requirements.txt        # Python dependencies
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── ticket.html
│   ├── new_ticket.html
│   ├── edit_ticket.html
│   ├── change_password.html
│   └── users.html
└── static/
└── css/
└── style.css

```

## Installation
```bash
git clone https://github.com/sabrinavsimmons/Deskflow.git
cd Deskflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python database.py
python app.py
```

Access the app at `http://localhost:5000`.

## Deployment

The app runs as a systemd service and starts automatically on boot.
```bash
sudo systemctl status deskflow
```

Access the app at `http://<server-ip>:5000` from any device on the network.

## Purpose

Built as a homelab portfolio project to demonstrate full-stack web development,
Linux server administration, database design, authentication, and self-hosted service deployment.
