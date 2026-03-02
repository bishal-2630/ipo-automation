---
title: IPO Automation Backend
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

# IPO Automation Backend (Django)

This is the backend for the IPO Automation Mobile App. It handles account management, logs, and automated IPO applications.

## Architecture
The automation system has been migrated from GitHub Actions to a server-side runtime for better reliability and mobile integration.

- **Backend**: Django REST Framework (hosted on Hugging Face).
- **Database**: Neon PostgreSQL (Production) / SQLite (Development).
- **Automation**: Playwright (Headless Chromium).
- **Scheduler**: Celery + Celery Beat (Redis Broker).

## Features
- **Centralized Management**: Manage multiple MeroShare accounts via the mobile app.
- **Automated Runs**: Fully automated daily checks at **4:15 PM NPT**.
- **Real-time Logs**: Application status and remarks are saved directly to the database.
- **Push Notifications**: Receive instant updates via Firebase Cloud Messaging (FCM).

## How it Works
Celery Beat triggers the `run_all_accounts_task` daily. The server fetches all active accounts from the database and uses Playwright to navigate MeroShare, apply for open "Ordinary Shares", and log the results.
