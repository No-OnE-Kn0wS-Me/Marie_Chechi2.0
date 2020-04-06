import hashlib
import os
import math
import urllib.request as urllib

from io import BytesIO
from PIL import Image

from typing import Optional, List
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError
from telegram import Update, Bot
from telegram.ext import CommandHandler, run_async
from telegram.utils.helpers import escape_markdown

from haruka import dispatcher
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.translations.strings import tld


@run_async
def stickerid(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            tld(chat.id, 'stickers_stickerid').format(
                escape_markdown(msg.reply_to_message.sticker.file_id)),
            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text(tld(chat.id, 'stickers_stickerid_no_reply'))


@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.send_document(chat_id, document=open('sticker.png', 'rb'))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text(tld(chat_id, 'stickers_getsticker_no_reply'))


@run_async
def kang(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    packnum = 0
    packname = "c" + str(user.id) + "_by_" + bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = "c" + str(packnum) + "_" + str(
                    user.id) + "_by_" + bot.username
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "kangsticker.png"
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text(tld(chat.id, 'stickers_kang_error'))
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')
        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"
        try:
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            if not msg.reply_to_message.sticker:
                im.save(kangsticker, "PNG")
            bot.add_sticker_to_set(user_id=user.id,
                                   name=packname,
                                   png_sticker=open('kangsticker.png', 'rb'),
                                   emojis=sticker_emoji)
            msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text(tld(chat.id, 'stickers_kang_only_img'))
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker.png', 'rb'),
                                  sticker_emoji, bot, packname, packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                bot.add_sticker_to_set(user_id=user.id,
                                       name=packname,
                                       png_sticker=open(
                                           'kangsticker.png', 'rb'),
                                       emojis=sticker_emoji)
                msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                    parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text(tld(chat.id, 'stickers_kang_invalid_emoji'))
            elif e.message == "Stickers_too_much":
                msg.reply_text(tld(chat.id, 'stickers_kang_too_much'))
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                    parse_mode=ParseMode.MARKDOWN)
            print(e)
    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🤔"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            msg.reply_photo(photo=open('kangsticker.png', 'rb'))
            bot.add_sticker_to_set(user_id=user.id,
                                   name=packname,
                                   png_sticker=open('kangsticker.png', 'rb'),
                                   emojis=sticker_emoji)
            msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text(tld(chat.id, 'stickers_kang_only_img'))
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker.png', 'rb'),
                                  sticker_emoji, bot, packname, packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                bot.add_sticker_to_set(user_id=user.id,
                                       name=packname,
                                       png_sticker=open(
                                           'kangsticker.png', 'rb'),
                                       emojis=sticker_emoji)
                msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                    parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text(tld(chat.id, 'stickers_kang_invalid_emoji'))
            elif e.message == "Stickers_too_much":
                msg.reply_text(tld(chat.id, 'stickers_kang_too_much'))
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                    parse_mode=ParseMode.MARKDOWN)
            print(e)
    else:
        packs = tld(chat.id, 'stickers_kang_no_reply')
        if packnum > 0:
            firstpackname = "c" + str(user.id) + "_by_" + bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[pack{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[pack](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("kangsticker.png"):
        os.remove("kangsticker.png")


def makepack_internal(msg, user, png_sticker, emoji, bot, packname, packnum):
    chat = update.effective_chat  # type: Optional[Chat]
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        success = bot.create_new_sticker_set(user.id,
                                             packname,
                                             f"{name}s haruka pack" +
                                             extra_version,
                                             png_sticker=png_sticker,
                                             emojis=emoji)
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text(
                tld(chat.id, 'stickers_pack_name_exists') % packname,
                parse_mode=ParseMode.MARKDOWN)
        elif e.message == "Peer_id_invalid":
            msg.reply_text(tld(chat.id, 'stickers_pack_contact_pm'),
                           reply_markup=InlineKeyboardMarkup([[
                               InlineKeyboardButton(text="Start",
                                                    url=f"t.me/{bot.username}")
                           ]]))
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
                parse_mode=ParseMode.MARKDOWN)
        return

    if success:
        msg.reply_text(tld(chat.id, 'stickers_kang_success').format(packname, sticker_emoji),
            parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text(tld(chat.id, 'stickers_pack_create_error'))


__help__ = True

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
KANG_HANDLER = DisableAbleCommandHandler("kang",
                                         kang,
                                         pass_args=True,
                                         admin_ok=True)

dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(KANG_HANDLER)
import os
import re
import requests
import urllib
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

from typing import List
from telegram import ParseMode, InputMediaPhoto, Update, Bot, TelegramError
from telegram.ext import run_async

from menhera import dispatcher

from menhera.modules.disable import DisableAbleCommandHandler


opener = urllib.request.build_opener()
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.38 Safari/537.36'
#useragent = 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
opener.addheaders = [('User-agent', useragent)]


@run_async
def reverse(bot: Bot, update: Update, args: List[str]):
    if os.path.isfile("okgoogle.png"):
        os.remove("okgoogle.png")

    msg = update.effective_message
    chat_id = update.effective_chat.id
    rtmid = msg.message_id
    imagename = "okgoogle.png"

    reply = msg.reply_to_message
    if reply:
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.photo:
            file_id = reply.photo[-1].file_id
        elif reply.document:
            file_id = reply.document.file_id
        else:
            msg.reply_text("Reply to an image or sticker to lookup.")
            return
        image_file = bot.get_file(file_id)
        image_file.download(imagename)
        if args:
            txt = args[0]
            try:
                lim = int(txt)
            except:
                lim = 2
        else:
            lim = 2
    elif args and not reply:
        splatargs = msg.text.split(" ")
        if len(splatargs) == 3:                
            img_link = splatargs[1]
            try:
                lim = int(splatargs[2])
            except:
                lim = 2
        elif len(splatargs) == 2:
            img_link = splatargs[1]
            lim = 2
        else:
            msg.reply_text("/reverse <link> <amount of images to return.>")
            return
        try:
            urllib.request.urlretrieve(img_link, imagename)
        except HTTPError as HE:
            if HE.reason == 'Not Found':
                msg.reply_text("Image not found.")
                return
            elif HE.reason == 'Forbidden':
                msg.reply_text("Couldn't access the provided link, The website might have blocked accessing to the website by bot or the website does not existed.")
                return
        except URLError as UE:
            msg.reply_text(f"{UE.reason}")
            return
        except ValueError as VE:
            msg.reply_text(f"{VE}\nPlease try again using http or https protocol.")
            return
    else:
        msg.reply_markdown("Please reply to a sticker, or an image to search it!\nDo you know that you can search an image with a link too? `/reverse [picturelink] <amount>`.")
        return

    try:
        searchUrl = 'https://www.google.com/searchbyimage/upload'
        multipart = {'encoded_image': (imagename, open(imagename, 'rb')), 'image_content': ''}
        response = requests.post(searchUrl, files=multipart, allow_redirects=False)
        fetchUrl = response.headers['Location']

        if response != 400:
            xx = bot.send_message(chat_id, "Image was successfully uploaded to Google."
                                  "\nParsing source now. Maybe.", reply_to_message_id=rtmid)
        else:
            xx = bot.send_message(chat_id, "Google told me to go away.", reply_to_message_id=rtmid)
            return

        os.remove(imagename)
        match = ParseSauce(fetchUrl + "&hl=en")
        guess = match['best_guess']
        if match['override'] and not match['override'] == '':
            imgspage = match['override']
        else:
            imgspage = match['similar_images']

        if guess and imgspage:
            xx.edit_text(f"[{guess}]({fetchUrl})\nLooking for images...", parse_mode='Markdown', disable_web_page_preview=True)
        else:
            xx.edit_text("Couldn't find anything.")
            return

        images = scam(imgspage, lim)
        if len(images) == 0:
            xx.edit_text(f"[{guess}]({fetchUrl})\n[Visually similar images]({imgspage})"
                          "\nCouldn't fetch any images.", parse_mode='Markdown', disable_web_page_preview=True)
            return

        imglinks = []
        for link in images:
            lmao = InputMediaPhoto(media=str(link))
            imglinks.append(lmao)

        bot.send_media_group(chat_id=chat_id, media=imglinks, reply_to_message_id=rtmid)
        xx.edit_text(f"[{guess}]({fetchUrl})\n[Visually similar images]({imgspage})", parse_mode='Markdown', disable_web_page_preview=True)
    except TelegramError as e:
        print(e)
    except Exception as exception:
        print(exception)

def ParseSauce(googleurl):
    """Parse/Scrape the HTML code for the info we want."""

    source = opener.open(googleurl).read()
    soup = BeautifulSoup(source, 'html.parser')

    results = {
        'similar_images': '',
        'override': '',
        'best_guess': ''
    }

    try:
         for bess in soup.findAll('a', {'class': 'PBorbe'}):
            url = 'https://www.google.com' + bess.get('href')
            results['override'] = url
    except:
        pass

    for similar_image in soup.findAll('input', {'class': 'gLFyf'}):
            url = 'https://www.google.com/search?tbm=isch&q=' + urllib.parse.quote_plus(similar_image.get('value'))
            results['similar_images'] = url

    for best_guess in soup.findAll('div', attrs={'class':'r5a77d'}):
        results['best_guess'] = best_guess.get_text()

    return results

def scam(imgspage, lim):
    """Parse/Scrape the HTML code for the info we want."""

    single = opener.open(imgspage).read()
    decoded = single.decode('utf-8')
    if int(lim) > 10:
        lim = 10

    imglinks = []
    counter = 0

    pattern = r'^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$'
    oboi = re.findall(pattern, decoded, re.I | re.M)

    for imglink in oboi:
        counter += 1
        imglinks.append(imglink)
        if counter >= int(lim):
            break

    return imglinks


__help__ = """
- /reverse: Does a reverse image search of the media which it was replied to.
"""

__mod_name__ = "Image Lookup"

REVERSE_HANDLER = DisableAbleCommandHandler("reverse", reverse, pass_args=True, admin_ok=True)

dispatcher.add_handler(REVERSE_HANDLER)
