#!/usr/bin/env python3

import json

fh = open('pets.json')
data=json.load(fh)

pets = {}

for k in data['animals']:
    try:
        print(f"##############\n{k['name']} {k['photos'][0]['medium']}")
        if 'Courtesy' in k['name']:
           continue
        k['name'] = k['name'].replace(' ', '')
        k['name'] = k['name'].replace('(', '_')
        k['name'] = k['name'].replace(')', '_')
        url=k['photos'][0]['medium']
        pets[k['name']]=url 
    except IndexError:
        print(f"{k['name']} has no photos")

with open('pets.wget.queue.txt','w') as fh:
    for k,v in pets.items():
        fh.write(f"{k}:{v}\n")
