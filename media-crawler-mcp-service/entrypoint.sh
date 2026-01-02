#!/bin/bash
set -e

if [ ! -f /app/.skip_chown ]; then
    chmod 777 /app/data 2>/dev/null || true
    chmod 777 /app/logs 2>/dev/null || true
    chmod 777 /app/browser_data 2>/dev/null || true
    chmod 777 /app/browser_data/* 2>/dev/null || true
    chown -R appuser:appgroup /app/data 2>/dev/null || true
    chown -R appuser:appgroup /app/logs 2>/dev/null || true
    chown -R appuser:appgroup /app/browser_data 2>/dev/null || true
    touch /app/.skip_chown
fi

exec "$@"
