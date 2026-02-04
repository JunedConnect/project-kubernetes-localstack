#!/bin/bash

set -euo pipefail

API_URL="${API_URL:-http://localhost:30080}"

test_health() {
    curl -s "${API_URL}/swagger/"
}

test_get_users() {
    curl -s "${API_URL}/users"
}

test_create_user() {
    local test_image="/tmp/test-avatar.png"
    echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$test_image"
    curl -X POST "${API_URL}/user" \
        -F "name=Test User" \
        -F "email=test-$(date +%s)@example.com" \
        -F "avatar=@${test_image}"
    rm "$test_image"
}


echo "Testing ${API_URL}"

test_health

test_get_users

test_create_user
