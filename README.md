# esp32-picbooth

## What is this?

Stream Possible Pet Pic Perpetually ...

<img src="images/pfinder.jpg"  width="200"/>

Uses the Pet Finder API - https://www.petfinder.com/developers/v2/docs/ 

## Why?
Guilt. Mostly. Get the pet you deserve!

## Requirements
- esp32
- Raspberry Pi or equivalent like EEE PC running linux
- 320x240 SPI Serial ILI9341 - https://www.amazon.com/dp/B09XHJ9KRX

## Setup
- In order to set this up you'll first install your esp32 on your wireless network and connect the ILI9341 screen to it.

- Since the esp32 is not powerful enough to process images and does not have the pillow package you'll need another computer like a Raspberry Pi to process the images. This machine will also be running Nginx to serve the raw data to the ESP32 for it to consume and send to its screen.


This is another outake from https://github.com/jouellnyc/ESP32-picbooth , more details there.

Configs / Libraries shared in https://github.com/jouellnyc/mcconfigs 
