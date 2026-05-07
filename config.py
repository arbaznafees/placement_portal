"""
Configuration file for the Placement Portal Application
This file contains all app settings and secret keys
"""
import os

class Config:
    # Secret key for session management (change this in production!)
    SECRET_KEY = 'your-secret-key-change-this-in-production'
    
    # Database configuration - SQLite database file
    SQLALCHEMY_DATABASE_URI = 'sqlite:///placement_portal.db'
    
    # Disable modification tracking to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for resume files
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
