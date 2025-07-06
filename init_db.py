#!/usr/bin/env python3
"""
Database initialization script for AI Resume Optimizer
Creates the necessary tables for user authentication and persistent data storage
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database with required tables"""
    
    # Create database connection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table with authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_sessions table for session management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create cover_letters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create writing_analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS writing_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            analysis TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create master_resume table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_resume (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("📊 Tables created:")
    print("   - users (authentication)")
    print("   - user_sessions (session management)")
    print("   - cover_letters (stored cover letters)")
    print("   - writing_analysis (writing style analysis)")
    print("   - master_resume (complete resume storage)")

if __name__ == "__main__":
    init_database() 