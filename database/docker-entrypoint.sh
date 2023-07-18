#!/bin/sh
# 30 June 2023 this command leads to bash: docker-entrypoint.sh: command not
# found. It exists because of legacy reasons
.sh text eol=lf

set -e
if [ "$1" = 'dataservice' ]; then
    echo "Launching workers"
    cd /runtime && celery -A worker worker -E --loglevel INFO --concurrency=4 --pool=threads &
    echo "Launching service"
    cd /runtime && exec python3 app.py
fi
#exec "$@"
