# config/settings.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME_AFV = os.getenv("DB_NAME_AFV")
    DB_NAME_PROTHEUS = os.getenv("DB_NAME_PROTHEUS")
    DB_DRIVER = os.getenv("DB_DRIVER")

    NEOGRID_USERNAME = os.getenv("NEOGRID_USERNAME")
    NEOGRID_PASSWORD = os.getenv("NEOGRID_PASSWORD")
    NEOGRID_URL = os.getenv("NEOGRID_URL")

settings = Settings()
