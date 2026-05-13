#!/bin/bash
cd "/Users/devesh/Documents/projects/Customer Support Ticketing/support-router"
source venv/bin/activate
export PATH="/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose up --build
