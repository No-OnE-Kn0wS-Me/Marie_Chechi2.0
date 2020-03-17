import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ആരേലും ഒരാളെ സൂചിപ്പിച്ചാൽ അല്ലെ എനിക്ക് ബണ്ണ് കൊടുക്കാൻ കഴിയൂ...")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("ഇങ്ങനെ ഒരാൾ ഇപ്പോൾ ജീവിച്ചിരിപ്പില്ലന്നു തോനുന്നു😅..")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("എനിക്ക് അഡ്മിൻസിന് ബണ്ണ് കൊടുക്കാൻ പറ്റൂല😔...")
        return ""

    if user_id == bot.id:
        message.reply_text("ഞാൻ എന്നെത്തന്നെ ബാൻ ചെയ്യാനോ... നടക്കുന്ന കാര്യം വല്ലതും പറ😂... ")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)

    reply = "{} ന് ബണ്ണ് കൊടുത്ത്‌വിട്ടിട്ടുണ്ട്.." .format(mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)
        reply += "\n<b>Reason:</b> <i>{}</i>".format(reason)

    try:
        chat.kick_member(user_id)
        keyboard = []
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('ബണ്ണ് കൊടുത്തിട്ടുണ്ട്...!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("എനിക്കയാൾക്കു ബണ്ണ് കൊടുക്കാൻ സാധിക്കില്ല..")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ ഒരു വ്യക്തിയെ സൂചിപ്പിക്കുന്നതായി തോന്നുന്നില്ല!.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("എനിക്ക് ഈ യൂസേറിനെ കണ്ടെത്താൻ കഴിയുന്നില്ല")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("എനിക്ക് ആഗ്രഹം ഒക്കെ ഉണ്ട് but നടക്കൂലല്ലോ😛...")
        return ""

    if user_id == bot.id:
        message.reply_text("എന്നെ ബാൻ ചെയ്യാനോ..😢? ഞാൻ...എന്നെ ബാൻ ചെയ്യൂല എനിക്ക് ബണ്ണ് വേണ്ടാ..😔")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to ban this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMPBAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>" \
          "\n<b>• Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                                                mention_html(member.user.id, member.user.first_name), 
                                                                             user_id, time_val)
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        keyboard = []
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = "{} has been temporarily banned for {}!".format(mention_html(member.user.id, member.user.first_name),time_val)
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned! User will be banned for {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("എനിക്കും അഡ്മിൻസിനെ പുറത്താക്കാൻ ആഗ്രഹം ഉണ്ട് പക്ഷെ നടകൂല😌...")
        return ""

    if user_id == bot.id:
        message.reply_text("ആഹ്.. പറ്റില്ലാന്നു പറഞ്ഞാ.. പാറ്റൂല")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} has been kicked!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)

        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>• Admin:</b> {}" \
              "\n<b>• User:</b> {}" \
              "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                      mention_html(user.id, user.first_name),
                                                      mention_html(member.user.id, member.user.first_name), user_id)
        if reason:
            log += "\n<b>• Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Well damn, I can't kick that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@loggable
def banme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("ആഹ്.. എനിക്ക് ആഗ്രഹം ഒക്കെ ഉണ്ട് but നീ ഒരു അഡ്മിൻ അല്ലെ!.")
        return

    res = update.effective_chat.kick_member(user_id)  
    if res:
        update.effective_message.reply_text("അതിനെന്താ.., ബണ്ണ് കൊടുത്തിട്ടുണ്ട്.")
        log = "<b>{}:</b>" \
              "\n#BANME" \
              "\n<b>User:</b> {}" \
              "\n<b>ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                    mention_html(user.id, user.first_name), user_id)
        return log
    
    else:
        update.effective_message.reply_text("എന്തോന്ന്? എന്നെ കൊണ്ടൊന്നും പറ്റൂല :/")
        
@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("ആഹ്.. എനിക്ക് ആഗ്രഹം ഒക്കെ ഉണ്ട് but നീ ഒരു അഡ്മിൻ അല്ലെ!.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("ആ ചെങ്ങായി ഇവിടെ ഉള്ളത് തന്നെ ആണോ? എനിക്ക് കാണാനില്ലല്ലോ user not found!😔")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("ഞാൻ ഇവിടെ ഇല്ലെങ്കിൽ എനിക്ക് എന്നെ എങ്ങനെ unban ചെയ്യാൻ പറ്റും😌...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("അറിയാൻ മേലത്തോണ്ടു ചോദിക്കുവാ ഈ ചാറ്റിൽ ഉള്ള ആളെ തന്നെ unban ചെയ്യാൻ നിങ്ങൾ എന്തിനാ ശ്രമിക്കുന്നെ..?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("ആഹ്... ഇനി ആ ചെങ്ങായിക്കു ഇവിടെ കയറാം!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                  mention_html(user.id, user.first_name),
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)

    return log

@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def sban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    
    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n#SILENT BAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)       
    return ""

__help__ = """
 - /kickme: കമാൻഡ് നൽകിയാൽ നിന്നെ നീ തന്നെ ചവിട്ടി പുറത്താകുന്നു😅..
 - /banme: കമാൻഡ് കൊടുത്താൽ നിന്നെ നീ ചവിട്ടി പുറത്താക്കി ലോക്ക് ഇടും.
 
*Admin only:*
 - /ban <userhandle>: ഒരു ഉപയോക്താവിനെ നിരോധിക്കുന്നു. (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി).
 - /sban <userhandle>: നിശബ്ദമായി ഒരു ഉപയോക്താവിനെ നിരോധിക്കുന്നു. (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി).
 - /tban <userhandle> x(m/h/d): സമയത്തേക്ക് ഒരു ഉപയോക്താവിനെ നിരോധിക്കുന്നു. (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി). m = മിനിറ്റ്, h = മണിക്കൂർ, d = ദിവസം.
 - /unban <userhandle>:  ഒരു ഉപയോക്താവിനെ നിരോധിക്കുന്നു. (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി).
 - /kick <userhandle>: ഒരു ഉപയോക്താവിനെ ചവിട്ടി പുറത്താക്കുന്നു, (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി).
"""

__mod_name__ = "Bans"

BAN_HANDLER = DisableAbleCommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.group)
SBAN_HANDLER = CommandHandler("sban", sban, pass_args=True, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
