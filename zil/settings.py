# app/settings.py
from datetime import timedelta

SECRET_KEY = "change-this-to-a-strong-random-string"  # <- change for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
