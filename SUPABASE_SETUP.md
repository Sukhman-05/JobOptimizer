# Supabase Setup Guide

## Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Sign up for a free account
3. Create a new project

## Step 2: Get Database Connection Details

1. In your Supabase dashboard, go to **Settings** → **Database**
2. Copy the **Connection string** (it looks like: `postgresql://postgres:[password]@[host]:5432/postgres`)

## Step 3: Set Environment Variables

### For Local Development
Create a `.env` file in your project root:
```
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
```

### For Vercel Deployment
In your Vercel dashboard, add these environment variables:
- `OPENAI_API_KEY` = your OpenAI API key
- `SECRET_KEY` = your secret key (any random string)
- `DATABASE_URL` = your Supabase connection string

## Step 4: Test the Setup

1. **Local Testing:**
   ```bash
   python3 app.py
   ```
   Visit `http://localhost:5001` and try to sign up

2. **Deploy to Vercel:**
   - Push your changes to GitHub
   - Vercel will automatically deploy
   - Test the signup/login functionality

## Database Schema

The app will automatically create these tables in Supabase:

- `users` - User accounts and authentication
- `user_sessions` - Session management  
- `cover_letters` - Stored cover letters
- `writing_analysis` - Writing style analysis
- `master_resume` - User's master resume

## Benefits

✅ **Data Persistence** - User data survives redeploys  
✅ **Cross-Device Access** - Users can log in from any device  
✅ **Scalable** - PostgreSQL can handle thousands of users  
✅ **Resume-Worthy** - PostgreSQL is industry standard  
✅ **Free Tier** - 500MB database, 50,000 monthly active users  

## Troubleshooting

### Connection Issues
- Verify your `DATABASE_URL` is correct
- Check that your Supabase project is active
- Ensure environment variables are set in Vercel

### Migration Issues
- The app automatically creates tables on first run
- No manual migration needed

### Performance
- Supabase is much faster than SQLite
- Automatic indexing and optimization
- Built-in connection pooling 