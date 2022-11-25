#!/usr/bin/env python3

""" Extract pet records and create a list of pets and photo urls to crawl in the next step """

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
        #Small pics seems easier to make larger than 
        #to make large pics to smaller for the ili9341 and underlying libraries 
        url=k['photos'][0]['small']
        pets[k['name']]=url 
    except IndexError:
        print(f"{k['name']} has no photos")

with open('pets.wget.queue.txt','w') as fh:
    for k,v in pets.items():
        fh.write(f"{k}:{v}\n")
