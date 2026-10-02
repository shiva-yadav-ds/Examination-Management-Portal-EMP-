# Universal WSGI entrypoint for production servers (Gunicorn, uWSGI, Render, Railway, etc.)
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
