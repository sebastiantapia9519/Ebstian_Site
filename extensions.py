"""Shared Flask extensions.

Keeping extensions outside app.py avoids circular imports between the app
and database models.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
