#from backend.app import jwt
from datetime import datetime, timedelta
from backend.app.models.user import User
from flask_jwt_extended import create_access_token


def create_access_token(identity, expires_delta=None):
    if expires_delta is None:
        expires_delta = timedelta(days=1)

    return create_access_token(identity=identity, expires_delta=expires_delta)
