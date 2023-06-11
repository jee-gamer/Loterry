#!/bin/sh
set -e
if [ "$1" = 'dataservice' ]; then
    echo "Launching workers"
    cd /database && celery -A worker worker -B --loglevel INFO &
    echo "Launching service"
    cd /database && exec python3 app.py
fi
#exec "$@"