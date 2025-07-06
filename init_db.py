#!/usr/bin/env python3
"""
Database initialization script for AI Resume Optimizer
Creates the necessary tables for user sessions and persistent data storage
"""

import sqlite3
import os

def init_database():
    """Initialize the database with required tables"""
    
    # Create database connection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create cover_letters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create writing_analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS writing_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            analysis TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_resume (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            content TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("📊 Tables created:")
    print("   - users (user sessions)")
    print("   - cover_letters (stored cover letters)")
    print("   - writing_analysis (writing style analysis)")
    print("   - master_resume (complete resume storage)")

if __name__ == "__main__":
    init_database() 