#!/bin/bash

CLIENT_ID="m5GdkTkyYoiRNJMYYz70o0dxuIk58qqCUlzBZFG5kBqIerjWIK"
CLIENT_SECRET="CnCZsmLh3WR1GGMS4Mg4ZYBl6KEdsydFLdZO88rm"

BR=$(curl -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" https://api.petfinder.com/v2/oauth2/token | cut -d ":" -f 4 | cut -d '}' -f 1 |  tr -d '"' )

limit=100
#what=dog
what=cat
curl -H "Authorization: Bearer ${BR}" "https://api.petfinder.com/v2/animals?type=${what}&size=small&location=11218&limit=${limit}" > pets.json
