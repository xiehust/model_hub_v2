#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: \$0 <api_key>"
    exit 1
fi

apikey=$1

pm2 start server.py --name chat-app --interpreter python3 -- --host 0.0.0.0 --port 8081 --api-keys $apikey
pm2 startup systemd
