# Diploma Study Hub – Karnataka DTE

A modern, student-centric academic resource platform designed to organize and provide free access to Karnataka Department of Technical Education (DTE) diploma notes, previous year question papers, lab manuals, syllabus copies, and exam preparation materials.

---

## 🚀 Features

- **Scheme-wise Navigation:** Structured support for **C-15**, **C-20**, and **C-25** schemes.
- **Branch & Semester Filtering:** Browse materials across 8 engineering disciplines:
  - Computer Science & Engineering (CSE)
  - Information Science & Engineering (ISE)
  - Electronics & Communication Engineering (ECE)
  - Electrical & Electronics Engineering (EEE)
  - Mechanical Engineering (MECH)
  - Civil Engineering (CIVIL)
  - Automobile Engineering (AUTO)
  - Other Diploma Branches (OTHER)
- **Subject & Unit Detail:** Unit-wise breakdown with in-browser PDF viewing, new-tab preview, and direct download links.
- **Contact Us & Support:**
  - Configurable inquiry channels for general support, technical issues, contributions, and feedback.
  - Fully functional contact form with client/server validation, honeypot spam protection, rate limiting, duplicate detection, and file attachment support (PDF, images, text up to 5 MB).
  - Background email delivery support (student acknowledgement + admin notification) with graceful fallback to database logging.
  - Frequently Asked Questions (FAQ) accordion.
- **About Us:** Platform overview, mission and vision, supported curriculum schemes, and developer credits.
- **Responsive & Accessible:** Built with semantic HTML5, Bootstrap 5, custom CSS design system, and screen-reader accessibility (`:user-invalid` synchronization and live region announcements).

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Django 5.2+
- **Database:** SQLite (development; planned migration to MySQL/PostgreSQL in later phases)
- **Frontend:** Django Templates, Vanilla JavaScript, CSS custom properties, Bootstrap 5.3, Bootstrap Icons
- **Storage:** Local media directory with UUID-based attachment management

---

## 📋 Prerequisites

- **Python 3.12+** installed and available on your PATH.
- **Git** for version control.

---

## ⚡ Quick Start / Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/Shilpajcer/Diploma-Study-Resources.git
cd Diploma-Study-Resources
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. (Optional) Create a superuser for Django Admin
```bash
python manage.py createsuperuser
```

### 6. Start the development server
```bash
python manage.py runserver 127.0.0.1:8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 📧 Email Configuration (Optional)

In development mode, contact submissions are stored in the database (`ContactSubmission` model) and mock emails are written locally to `sent_emails/`.

To deliver real notifications to your inbox (e.g. Gmail), set the following environment variables before starting `runserver`:

```powershell
$env:EMAIL_HOST = "smtp.gmail.com"
$env:EMAIL_PORT = "587"
$env:EMAIL_USE_TLS = "True"
$env:EMAIL_HOST_USER = "your-email@gmail.com"
$env:EMAIL_HOST_PASSWORD = "your-16-char-app-password"
$env:DEFAULT_FROM_EMAIL = "your-email@gmail.com"
$env:CONTACT_ADMIN_EMAIL = "your-email@gmail.com"
```

---

## 🧪 Running Automated Tests

Run the full Django test suite:
```bash
python manage.py test apps.core -v 2
```

---

## 📁 Project Structure

```text
diploma-study-hub/
├── apps/
│   └── core/                 # Core application (views, models, forms, tests)
│       ├── migrations/       # Database migrations
│       ├── admin.py          # Django Admin registration
│       ├── forms.py          # Contact form & file validation
│       ├── models.py         # Schemes, Branches, Semesters, Subjects, Resources, ContactSubmission
│       ├── urls.py           # Application routes
│       └── views.py          # View functions & API endpoints
├── config/
│   ├── settings/
│   │   ├── base.py           # Shared settings & environment configuration
│   │   └── dev.py            # Development settings
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py               # WSGI entrypoint
├── media/                    # Uploaded study materials & attachments (git-ignored)
├── static/
│   ├── css/                  # Base styles, variables, component styles, pages
│   └── js/                   # Main JS & contact form handling
├── templates/
│   ├── components/           # Navbar, footer, branch & resource cards
│   └── public/               # Home, materials, subject detail, about, contact, 404
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📄 License & Disclaimer

This project is an independent educational student resource and is not officially affiliated with or endorsed by the Department of Technical Education (DTE), Karnataka. All trademarks and official curricula belong to their respective authorities.
