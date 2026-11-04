KEYNOVA 

A premium mechanical keyboard e-commerce platform built with Python and Django.

KEYNOVA is a dark-themed online keyboard store with a clean shopping experience, a session-based cart, user accounts, and a manual payment flow designed (KBZPay, Wave, AYA Pay, bank transfer, or cash on delivery). Prices are shown in Myanmar Kyat (Ks).

Project status: Live and deployed 

 Live site: https://keynova-pwxt.onrender.com

#Features

Product catalog and product detail pages with variants, specs, and images
Prices in Myanmar Kyat (Ks)
Session-based shopping cart
User registration, login, and logout
Account page with profile editing and password change

Checkout with five payment options:
Cash on delivery
KBZPay, Wave, AYA Pay, and bank transfer (manual payment)
Manual payment flow: the customer sees the shop's account details and the exact amount, then submits a transaction ID and an optional screenshot
Admin actions to mark payments as paid or rejected
Order history with a progress tracker and payment status
Stock is deducted when an order is placed
Product images and payment screenshots stored on Cloudinary in production
Responsive dark-themed user interface


Tech Stack
Backend: Python, Django 5.2
API: Django REST Framework
Database: SQLite (local development), PostgreSQL on Neon (production)
Media storage: Local media/ folder (development), Cloudinary (production)
Static files: WhiteNoise
Server: Gunicorn
Hosting: Render
Frontend: HTML, CSS, JavaScript, Django Templates
Version Control: Git and GitHub
Getting Started (local development)


1. Clone the repository
bash
git clone https://github.com/Robert-KSik/KEYNOVA.git
cd KEYNOVA

2. Create and activate a virtual environment

Windows (PowerShell):

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

macOS / Linux:

bash
python3 -m venv .venv
source .venv/bin/activate



3. Install dependencies
bash
python -m pip install -r requirements.txt



4. Configure environment variables

dotenv
DJANGO_SECRET_KEY="ayn cx mae koko sik"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost





5. Set up the database
bash
python manage.py migrate
python manage.py createsuperuser



6. Payment details

KBZPay- 09784688536
Wave - 09784688536
AYA Pay -09784688536
Bank details- XXXXXXXXXXX



7. Start the development server
bash
python manage.py runserver

Open http://127.0.0.1:8000/ in your browser. Add products from the admin panel at http://127.0.0.1:8000/admin/.

Environment Variables
Variable	Used for	Required in production
DJANGO_SECRET_KEY	Django's secret key	Yes
DJANGO_DEBUG	True for development, False in production	Yes
DJANGO_ALLOWED_HOSTS	Comma-separated allowed hosts	Optional (Render's hostname is added automatically)
DJANGO_CSRF_TRUSTED_ORIGINS	Comma-separated trusted origins	Optional
DATABASE_URL	PostgreSQL connection string	Yes
CLOUDINARY_URL	Cloudinary storage for uploaded images	Yes
DJANGO_SUPERUSER_USERNAME / EMAIL / PASSWORD	Creates the admin account on first deploy	Yes (first deploy)



Deployment (Render)
Build command:
bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && (python manage.py createsuperuser --noinput || true)



Start command:
bash
  gunicorn config.wsgi:application
Render redeploys automatically on every push to main.
The free Render plan sleeps after 15 minutes of inactivity, so the first request after a pause can take about 30 seconds.


Payment Flow
The customer chooses a payment method at checkout.
Cash on delivery goes straight to the order confirmation page.
For KBZPay, Wave, AYA Pay, or bank transfer, the customer is taken to a payment page showing the shop's account details and the exact amount.
The customer sends the money, then submits the transaction ID and an optional screenshot.
The order moves to "payment submitted." An admin checks the payment and marks it Paid or Rejected from the Django admin.
If rejected, the customer can submit their details again from the My Orders page.



Project Structure


text
KEYNOVA/
├── config/       # Django project settings, URLs, and media storage backend
├── products/     # Product catalog and detail pages
├── cart/         # Session-based shopping cart
├── accounts/     # Registration, login, profile editing, password change
├── orders/       # Checkout, payments, order history, admin actions
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md




Roadmap

 Initial Django project setup
 Product catalog and detail pages
 GitHub repository setup
 Shopping cart
 User registration, authentication, and profile editing
 Order management and checkout
 Manual payment system (KBZPay, Wave, AYA Pay, bank transfer, cash on delivery)
 Myanmar Kyat (Ks) pricing
 Deployment (Render, Neon PostgreSQL, Cloudinary)
 Search, filtering, and sorting
 Automated tests
 Restore stock automatically when an unpaid order is cancelled
 Email notifications for order and payment updates




What I Learned

This project is part of my backend development journey. Building it taught me:

Django architecture: apps, models, views, forms, and templates
Database design, migrations, and keeping schema changes in sync with the code
HTTP requests, sessions, cookies, and CSRF protection
Moving from SQLite to PostgreSQL and storing media on a cloud service
Keeping secrets in environment variables instead of in code
Deploying a real application and debugging it in production
Using dry runs before running commands that change live data
Author

Sikdev

GitHub: @Robert-KSik

Built with Python, Django, and a commitment to learning backend engineering.