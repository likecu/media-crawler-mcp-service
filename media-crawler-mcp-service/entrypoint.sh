#!/bin/bash
set -e

mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /app/browser_data/{xhs,bili,bili_qrcode,dy,ks,wb}
chmod 777 /app/browser_data
chmod 777 /app/browser_data/*

exec "$@"
