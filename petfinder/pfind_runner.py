import urequests
import machine
import utime as  time
import framebuf
import base64
import math

my_sleep=30

def custom_to_buff(data):
    width = data[0]
    height = data[1]
    return framebuf.FrameBuffer(data[2:],width,height, framebuf.MONO_HLSB)
      
def show_image(image,display):
    display.blit(image, 0, 0)
    display.show()

displayt='ili9341'
show_name = True

import gc
gc.collect()

print(f"Display is {displayt}")
if displayt == 'ili9341':
    
    from hardware.esp32_oled_2_8_inch import display, black, white, date_font,sm_font
    from .get_raw_image_nginx import get_file, get_size, get_name_file 

    while True:
        
        try:

            get_file()
            width,height = get_size()
            print(width,height)
            width=int(width)
            height=int(height)
            name = get_name_file()

            if height > 239:
                height=239
                print("height reduced to  239")

            display.clear()
            display.draw_image('/256.my_photo.jpg.raw', 0, 0, width, height)
            if show_name:
                display.draw_text(0, 0, name, date_font,  white , black)
        except Exception as e:
            print(e)
        print(f"sleeping {my_sleep}")
        time.sleep(my_sleep)            

else:

    while True:

        try:
            ziva = str(urequests.get('http://192.168.0.94:5000/picbooth/').text)
            print('Got it!')
        except:       
            ziva='gGD//////////////////4AA//////////////////+EAP//////////////////hgD//////////////////4YA//////////////////+GAP//////////////////DwD//////////////////x8A//////////////////8fAP//////////////////H4D//////////////////x+A//////////////////8fwP/////////////////+H8D//////////////////h/A//////////////////4/4P/////////////////+P+D//////////////////D/g//////////////////w/4P/////////////////8P/D//////////////////H/w//////////////////h/8P/////////////////wf/j/////////////////4H/4/////////////////8B/+P////////////////+Af/j/////////////////gD/8/////////////////4A//P/////////////////AP/7/////////////////wD/+////////////////v8A//v//////////////wAPAP/7//////////////gAAwD////////////////0AAEAf///////////////4AAAAH///////////////+AAAAB////////////////AAAAAf///////////////gAAAAH///////////////wAAAAA///////////////8AAAAAP//////////////+AOAAAD///////////////gf4AAA///////////////4D8AAAP//////////////+B/wAAD///////////////gf4AAA///////////////4H8AAAH//////////////+GjAAAB///////////////hgAAAAf//////////////8AAAAAH//////////////4AAAAAB//////////////+AAAAAAf////7QQAD/////wAAAAAH/4AAAAAAA/////8AAAAAA/+AAAAAAAP////+AAAAAAP/gAAAA////////gAAAAAD/wAAAAP///////4AAEAAA/+AAAAD////////CAAAAAP/gAAAA////////4AAAAAD/4AAAAf///////+AAAAAA/+AAAAH////////gAAAAAP/gAAAB////////8AAABAD/wAAAAf////////AAAAQAf8AAAAH////////4AAAIAH/AAAAB////////8AAACAB/wAAAAf////////AAABgAf8AAAAP////////wAAAYAH/AAAAD////////8AAAOAB/wAAAA////////+AAAHgAP8AAAAP///////xgAAD8MH/AAAAD///////hwAAB/CA/wAAAA///////AYAAAfwAf8AAAAP/////+AGAAAP8AH/AAAAD/////8AAAAAD/AB/wAAAA/////wAAAAAAfgAP8AAAAP////gAAAAAAB4AD/AAAAD////AAAAAAAAAAB/wAAAA////gAAAAAAAAAAP8AAAAP///wAAAAAAAAAAD/AAAAD///8AAAAAAAAAAA/wAAAA///+AAAAAAAAAAAPwAAAAP///AAAAAAAAAAADwAAAAD///wAAAAAAAAAABgAAAAB///4AAAAAAAAAAAAAAAAAP//+AAAAAAAAAAAAAAAAAAAAPAAAAAAAAAAAAAAAAAAAABwAAAAAAAAAAAAAAAAAAAAYAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
        finally:
            ziva_image = custom_to_buff(bytearray(base64.b64decode(ziva)))
            if displayt == 'oled':
                from hardware.oled_setup import oled as display
                show_image(ziva_image)
            if displayt == '2oleds':
                from hardware.oled_setup import oled1, oled2
                show_image(ziva_image, oled1)
                show_image(ziva_image, oled2)
        print(f"sleeping {my_sleep}")
        time.sleep(my_sleep)    
    
    