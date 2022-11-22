#!/bin/bash

""" Pull data from the Pet Finder API and save to .json file"""
""" https://www.petfinder.com/developers/v2/docs/ """

CLIENT_ID="XXXXXXXXXX"
CLIENT_SECRET="YYYYYY"

BR=$(curl -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" https://api.petfinder.com/v2/oauth2/token | cut -d ":" -f 4 | cut -d '}' -f 1 |  tr -d '"' )


what=cat
limit=100
size=small
zip_code=ZZZZ

curl -H "Authorization: Bearer ${BR}" "https://api.petfinder.com/v2/animals?type=${what}&size=${size}&location=${zip_code}&limit=${limit}" > pets.json
