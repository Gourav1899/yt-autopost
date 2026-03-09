"""
Supabase Client — Database connection
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")  # Service role key (admin access)

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL aur SUPABASE_SERVICE_KEY set karo .env mein!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
