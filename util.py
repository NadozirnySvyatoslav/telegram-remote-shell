#!/usr/bin/python
# -*- coding: utf-8 -*-



def is_compatible(platforms=['win32','linux2','darwin'], module=None):
    """
    Verify that a module is compatible with the host platform

    `Optional`
    :param list platforms:   compatible platforms
    :param str module:       name of the module

    """
    import sys
    if sys.platform in platforms:
        return True
    log("module {} is not yet compatible with {} platforms".format(module if module else '', sys.platform), level='warn')
    return False


def platform():
    """
    Return the system platform of host machine

    """
    import sys
    return sys.platform


def public_ip():
    """
    Return public IP address of host machine

    """
    import sys
    if sys.version_info[0] > 2:
        from urllib.request import urlopen
    else:
        from urllib import urlopen
    return urlopen('http://api.ipify.org').read()


def local_ip():
    """
    Return local IP address of host machine

    """
    import socket
    return socket.gethostbyname(socket.gethostname())


def mac_address():
    """
    Return MAC address of host machine

    """
    import uuid
    return ':'.join(hex(uuid.getnode()).strip('0x').strip('L')[i:i+2] for i in range(0,11,2)).upper()


def architecture():
    """
    Check if host machine has 32-bit or 64-bit processor architecture

    """
    import struct
    return int(struct.calcsize('P') * 8)


def device():
    """
    Return the name of the host machine

    """
    import socket
    return socket.getfqdn(socket.gethostname())


def username():
    """
    Return username of current logged in user

    """
    import os
    return os.getenv('USER', os.getenv('USERNAME', 'user'))


def administrator():
    """
    Return True if current user is administrator, otherwise False

    """
    import os
    import ctypes
    return bool(ctypes.windll.shell32.IsUserAnAdmin() if os.name == 'nt' else os.getuid() == 0)


def geolocation():
    """
    Return latitute/longitude of host machine (tuple)
    """
    import sys
    import json
    if sys.version_info[0] > 2:
        from urllib.request import urlopen
    else:
        from urllib2 import urlopen
    response = urlopen('http://ipinfo.io').read()
    json_data = json.loads(response)
    latitude, longitude = json_data.get('loc').split(',')
    return (latitude, longitude)



def unzip(filename):
    """
    Extract all files from a ZIP archive

    `Required`
    :param str filename:     path to ZIP archive

    """
    import os
    import zipfile
    z = zipfile.ZipFile(filename)
    path = os.path.dirname(filename)
    z.extractall(path=path)




def registry_key(key, subkey, value):
    """
    Create a new Windows Registry Key in HKEY_CURRENT_USER

    `Required`
    :param str key:         primary registry key name
    :param str subkey:      registry key sub-key name
    :param str value:       registry key sub-key value

    Returns True if successful, otherwise False

    """
    try:
        import _winreg
        reg_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, key, 0, _winreg.KEY_WRITE)
        _winreg.SetValueEx(reg_key, subkey, 0, _winreg.REG_SZ, value)
        _winreg.CloseKey(reg_key)
        return True
    except Exception as e:
        log(e)
        return False


def png(image):
    """
    Transforms raw image data into a valid PNG data

    `Required`
    :param image:   `numpy.darray` object OR `PIL.Image` object

    Returns raw image data in PNG format

    """
    import sys
    import zlib
    import numpy
    import struct

    try:
        from StringIO import StringIO  # Python 2
    except ImportError:
        from io import StringIO        # Python 3

    if isinstance(image, numpy.ndarray):
        width, height = (image.shape[1], image.shape[0])
        data = image.tobytes()
    elif hasattr(image, 'width') and hasattr(image, 'height') and hasattr(image, 'rgb'):
        width, height = (image.width, image.height)
        data = image.rgb
    else:
        raise TypeError("invalid input type: {}".format(type(image)))

    line = width * 3
    png_filter = struct.pack('>B', 0)
    scanlines = b"".join([png_filter + data[y * line:y * line + line] for y in range(height)])
    magic = struct.pack('>8B', 137, 80, 78, 71, 13, 10, 26, 10)

    ihdr = [b"", b'IHDR', b"", b""]
    ihdr[2] = struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0)
    ihdr[3] = struct.pack('>I', zlib.crc32(b"".join(ihdr[1:3])) & 0xffffffff)
    ihdr[0] = struct.pack('>I', len(ihdr[2]))

    idat = [b"", b'IDAT', zlib.compress(scanlines), b""]
    idat[3] = struct.pack('>I', zlib.crc32(b"".join(idat[1:3])) & 0xffffffff)
    idat[0] = struct.pack('>I', len(idat[2]))

    iend = [b"", b'IEND', b"", b""]
    iend[3] = struct.pack('>I', zlib.crc32(iend[1]) & 0xffffffff)
    iend[0] = struct.pack('>I', len(iend[2]))

    fileh = StringIO()
    fileh.write(str(magic))
    fileh.write(str(b"".join(ihdr)))
    fileh.write(str(b"".join(idat)))
    fileh.write(str(b"".join(iend)))
    fileh.seek(0)
    output = fileh.getvalue()
    if sys.version_info[0] > 2:
        output = output.encode('utf-8') # python3 compatibility
    return output


def delete(target):
    """
    Tries to delete file via multiple methods, if necessary

    `Required`
    :param str target:     target filename to delete

    """
    import os
    import shutil
    try:
        _ = os.popen('attrib -h -r -s {}'.format(target)) if os.name == 'nt' else os.chmod(target, 777)
    except OSError: pass
    try:
        if os.path.isfile(target):
            os.remove(target)
        elif os.path.isdir(target):
            import shutil
            shutil.rmtree(target, ignore_errors=True)
    except OSError: pass


def clear_system_logs():
    """
    Clear Windows system logs (Application, security, Setup, System)

    """
    try:
        for log in ["application","security","setup","system"]:
            output = powershell("& { [System.Diagnostics.Eventing.Reader.EventLogSession]::GlobalSession.ClearLog(\"%s\")}" % log)
            if output:
                log(output)
    except Exception as e:
        log(e)

