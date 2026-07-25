#!/bin/sh
set -e
echo ">>> Running migrations..."
flask db upgrade || echo ">>> upgrade failed, continuing to start"
exec "$@"