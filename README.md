# DeskFlow — Self-Hosted IT Ticketing System

A lightweight IT help desk ticketing system built with Python, Flask, and SQLite.
Deployed on a Ubuntu Server 24.04 VM running in a Proxmox homelab environment.

## Features

- Create, view, and update support tickets
- Priority levels: low, medium, high, critical
- Status tracking: open, in progress, resolved, closed
- Activity thread with timestamped notes per ticket
- Live dashboard with open, in-progress, resolved, and critical counts

## Tech Stack

- **Backend:** Python 3.12, Flask 3.1, SQLite
- **Frontend:** Jinja2 templates, HTML/CSS
- **Server:** Gunicorn 25.3
- **Process management:** systemd
- **Infrastructure:** Ubuntu Server 24.04 VM on Proxmox VE

## Project Structure
```

ticketing-app/
├── app.py            # Flask routes and application logic
├── database.py       # SQLite database setup and connection
├── tickets.db        # SQLite database file
├── templates/        # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── ticket.html
│   └── new_ticket.html
└── static/
    └── css/
        └── style.css
```

## Deployment

The app runs as a systemd service and starts automatically on boot.
```bash
sudo systemctl status deskflow
```

Access the app at `http://<server-ip>:5000` from any device on the network.

## Purpose

Built as a homelab portfolio project to demonstrate full-stack web development,
Linux server administration, database design, and self-hosted service deployment.
