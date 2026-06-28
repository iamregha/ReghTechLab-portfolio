"""
portfolio/analytics.py
======================
Lightweight view-tracking helper.

Design decisions:
  - Privacy-first: raw IPs are never stored. SHA-256 hashed only.
  - 24-hour deduplication window: refreshing a page does not inflate counts.
  - Swallows all exceptions silently - analytics should NEVER crash a page load.
"""
from datetime import datetime, timezone, timedelta

from .extensions import db
from .models import PostView


def record_view(post_id: int, request) -> None:
    """
    Record a unique view for ``post_id`` from the current request IP.

    Deduplication: if the same hashed IP already has a PostView row for
    this post created within the last 24 hours, no new row is inserted.

    Args:
        post_id:  The primary key of the Post being viewed.
        request:  The Flask request object (used to extract visitor IP).
    """
    try:
        # X-Forwarded-For is set by reverse proxies (nginx, Railway).
        # Fall back to direct remote address for local/Docker dev.
        raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
        # Take the leftmost IP when there is a chain: "client, proxy1, proxy2"
        raw_ip = raw_ip.split(",")[0].strip()

        ip_hash = PostView.hash_ip(raw_ip)
        cutoff  = datetime.now(timezone.utc) - timedelta(hours=24)

        already_viewed = db.session.execute(
            db.select(PostView).filter(
                PostView.post_id  == post_id,
                PostView.ip_hash  == ip_hash,
                PostView.viewed_at >= cutoff,
            )
        ).scalar_one_or_none()

        if not already_viewed:
            db.session.add(PostView(post_id=post_id, ip_hash=ip_hash))
            db.session.commit()

    except Exception:
        # Never let analytics fail a page load.
        db.session.rollback()
