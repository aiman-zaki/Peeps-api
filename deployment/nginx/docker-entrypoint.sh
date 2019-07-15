#!/bin/bash
set -e

if [ "$1" = 'supervisord' ]; then
    exec /usr/bin/supervisord
fi

exec "$@"