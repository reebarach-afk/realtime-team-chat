# Real-time Team Chat (Django Channels + React)

Rooms, live messaging over WebSockets, JWT auth, and admin/member roles.

## Run the backend (Windows PowerShell)
    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## Run the frontend (new terminal)
    cd frontend
    npm install
    copy .env.example .env
    npm run dev

Open http://localhost:5173

## Run backend tests
    cd backend
    python manage.py test

## Optional: use Redis as the channel layer
    docker run -d --name redis -p 6379:6379 redis:7
Then set REDIS_HOST=localhost in backend/.env and restart the server.
