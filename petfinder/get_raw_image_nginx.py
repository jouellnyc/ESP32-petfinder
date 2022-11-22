import mrequests
host = 'http://192.168.0.94:8080'

def get_name_file(filename='/name.txt'):
    try:
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"text/html"})
        if r.status_code == 200:
            r.save(filename)
            print("Name file saved to '{}'.".format(filename))
        else:
            print("Name file Request failed. Status: {}".format(r.status_code))
        r.close()
        
        with open(filename) as fh:
            contents=fh.read()
            return contents.strip()
        
    except Exception as e:
        print(f"Name file File Get failed. try again",e)
        pass


def get_file(filename='/256.my_photo.jpg.raw'):
    try:
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"image/png"})
        if r.status_code == 200:
            r.save(filename)
            print("Image saved to '{}'.".format(filename))
        else:
            print("Request failed. Status: {}".format(r.status_code))
        r.close()
    except:
        print(f"File Get failed. try again",e)
        pass

def get_size(filename='/filesize.txt'):
    
    try:
        
        url = host + filename
        r = mrequests.get(url, headers={b"accept": b"text/html"})
        if r.status_code == 200:
            r.save(filename)
            print("File saved to '{}'.".format(filename))
        else:
            print("Request failed. Status: {}".format(r.status_code))
        r.close()

        with open(filename) as fh:
            contents=fh.read()
            width, height = contents.split(':')
        return width,height
                
    except Exception as e:
        print(f"File size HTTP Get failed. try again",e)
        pass
    