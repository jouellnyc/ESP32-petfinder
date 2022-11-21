#!/bin/bash

CLIENT_ID="XXXXXXXXXX"
CLIENT_SECRET="YYYYYY"

BR=$(curl -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" https://api.petfinder.com/v2/oauth2/token | cut -d ":" -f 4 | cut -d '}' -f 1 |  tr -d '"' )

limit=100
what=cat

curl -H "Authorization: Bearer ${BR}" "https://api.petfinder.com/v2/animals?type=${what}&size=small&location=11218&limit=${limit}" > pets.json
