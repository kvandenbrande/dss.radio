#!/bin/sh

python server.py \
    --ice_password="PASSWORD" \
    --ice_host="icecast" \
    --ice_port=8000 \
    --ice_mount="/dss" \
    --api_host="api.deepsouthsounds.com" \
    --twitter_consumer_key="CONSUMER_KEY" \
    --twitter_consumer_secret="CONSUMER_SECRET" \
    --twitter_access_token="ACCESS_TOKEN" \
    --twitter_access_token_secret="ACCESS_TOKEN_SECRET"
