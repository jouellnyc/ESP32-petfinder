import mrequests
host = 'http://192.168.0.94:8080'

def get_name_file(filename='/name.txt'):
    try:
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"text/html"})
        if r.status_code == 200:
            r.save(filename)
            print(f"Name file saved to '{filename}'.")
        else:
            print(f"Name file Request failed. Status: {r.status_code}")
        r.close()

        with open(filename) as fh:
            contents=fh.read()
            return contents.strip()

    except Exception as e:
        print("Name file File Get failed. try again", e)


def get_file(filename='/256.my_photo.jpg.raw'):
    try:
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"image/png"})
        if r.status_code == 200:
            r.save(filename)
            print(f"Image saved to '{filename}'.")
        else:
            print(f"Request failed. Status: {r.status_code}")
        r.close()
    except:
        print("File Get failed. try again", e)

def get_size(filename='/filesize.txt'):
    
    try:
        
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"text/html"})
        if r.status_code == 200:
            r.save(filename)
            print(f"File saved to '{filename}'.")
        else:
            print(f"Request failed. Status: {r.status_code}")
        r.close()

        with open(filename) as fh:
            contents=fh.read()
            width, height = contents.split(':')
        return width,height

    except Exception as e:
        print("File size HTTP Get failed. try again", e)
    