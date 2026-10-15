# KEYNOVA ⌨️

A premium mechanical keyboard e-commerce platform built with Python and Django.

KEYNOVA is a dark-themed online keyboard store designed to provide a clean shopping experience, organized product information and a foundation for e-commerce functionality.

> **Project status:** In development 🚧

## Features

- Product catalog and product detail pages
- Keyboard information, including price, category, layout and connection type
- Product images managed through Django Admin
- Session-based shopping cart — in development
- Responsive dark-themed user interface

## Tech Stack

- **Backend:** Python, Django
- **API:** Django REST Framework
- **Database:** SQLite
- **Frontend:** HTML, CSS, Django Templates
- **Version Control:** Git and GitHub

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Robert-KSik/KEYNOVA.git
cd KEYNOVA
```

### 2. Create and activate a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install Django djangorestframework python-dotenv Pillow
```

### 4. Configure environment variables

Create a `.env` file in the project root and add your own development settings:

```dotenv
DJANGO_SECRET_KEY="your-own-secret-key"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Never commit your real `.env` file or secret key.

### 5. Set up the database

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Project Structure

```text
KEYNOVA/
├── config/       # Django project settings and URLs
├── products/     # Product catalog and detail pages
├── cart/         # Shopping cart functionality
├── accounts/     # Account-related functionality
├── manage.py
├── .gitignore
└── README.md
```

## Roadmap

- [x] Initial Django project setup
- [x] Product catalog and detail pages
- [x] GitHub repository setup
- [ ] Complete and test shopping cart
- [ ] User registration and authentication
- [ ] Search, filtering, and sorting
- [ ] Order management and checkout
- [ ] Automated tests
- [ ] Deployment

## Learning Goals

This project is part of my backend development journey. It helps me practice Django architecture, database relationships, HTTP requests, session management, security, testing, and version control.

## Author

**Sikdev**

GitHub: [@Robert-KSik](https://github.com/Robert-KSik)

---

*Built with Python, Django, and a commitment to learning backend engineering.*