"""Separate researcher credentials from opaque assignment credentials."""
import hmac
import os
from fastapi import Header, HTTPException
from sqlalchemy import inspect, text
from database import engine


def configured_key():
    value=os.environ.get('PRIVACYGUARD_RESEARCH_KEY','')
    return value if len(value)>=32 else None


def require_admin(x_research_key: str | None = Header(default=None)):
    secret=configured_key()
    if secret is None: raise HTTPException(503,'Configure PRIVACYGUARD_RESEARCH_KEY with at least 32 characters before research review.')
    if not x_research_key or not hmac.compare_digest(secret,x_research_key): raise HTTPException(403,'Researcher credential required.')


def assignments_exist():
    # Protect a previously configured database even after a server loses its key.
    with engine.connect() as connection:
        if not inspect(connection).has_table('benchmark_review_assignments'): return False
        return connection.execute(text('SELECT 1 FROM benchmark_review_assignments LIMIT 1')).first() is not None
