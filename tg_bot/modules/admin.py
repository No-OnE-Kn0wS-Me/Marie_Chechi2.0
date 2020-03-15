import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
def promote(bot: Bot, update: Update, args: List[str]) -> str:
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("നിനക്ക് കണ്ണിനു വല്ല കുഴപ്പം ഉണ്ടോടെയ്😏😏... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text("How am I meant to promote someone that's already an admin?")
        return ""

    if user_id == bot.id:
        message.reply_text("സേട്ടാ! എനിക്ക് എന്നെ തന്നെ പ്രൊമോട്ട് ചെയ്യാൻ കഴിയൂല. വേറെ ആരേലും ചെയ്യേണ്ടി വരും😅.")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(chat_id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          # can_invite_users=bot_member.can_invite_users,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages,
                          can_promote_members=bot_member.can_promote_members)

    message.reply_text("ആഹ് മൂപ്പർക്ക് സ്ഥാനക്കയറ്റം കൊടുത്തിട്ടുണ്ട്! 👍🏻")
    return "<b>{}:</b>" \
           "\n#PROMOTED" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
def demote(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("നിനക്ക് കണ്ണിനു വല്ല കുഴപ്പം ഉണ്ടോടെയ്😏😏....")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text("അഡ മോനെ ഇതൊന്നും അത്ര നല്ലതല്ല കെട്ടോ🤒🤒🤒")
        return ""

    if not user_member.status == 'administrator':
        message.reply_text("അയാളെ പ്രൊമോട്ട് ചെയ്താൽ അല്ലെ സെർ എനിക്ക് demote ചെയ്യാൻ പറ്റു😏!")
        return ""

    if user_id == bot.id:
        message.reply_text("ആഹ്! ബെസ്റ്റ് ചത്താലും ഞാൻ അത് ചെയ്യൂല😐.")
        return ""

    try:
        bot.promoteChatMember(int(chat.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text("Successfully demoted!")
        return "<b>{}:</b>" \
               "\n#DEMOTED" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}".format(html.escape(chat.title),
                                          mention_html(user.id, user.first_name),
                                          mention_html(user_member.user.id, user_member.user.first_name))

    except BadRequest:
        message.reply_text("എനിക്ക് പറ്റുമെന്ന് തോന്നുന്നില്ല മച്ചാനെ!😔. ഒന്നെങ്കിൽ ഞാൻ അഡ്മിൻ ആയിരിക്കില്ല, അല്ലേൽ വേറെ ഏതേലും ചെങ്ങായി ആകും പ്രൊമോട്ട് ചെയ്തത് "
                           "അതോണ്ട് എനിക്ക്‌ ഒന്നും ചെയ്യാൻ കഴിയൂല ")
        return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(bot: Bot, update: Update, args: List[str]) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return "<b>{}:</b>" \
               "\n#PINNED" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(bot: Bot, update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))


@run_async
@bot_admin
@user_admin
def invite(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text("എനിക്ക് അതിനുള്ള അധികാരം ഇപ്പൊ ഇല്ല! എന്റെ പേർമിഷൻസ് ആദ്യം മാറ്റ് അപ്പൊ നോക്കാം!")
    else:
        update.effective_message.reply_text("എനിക്ക് സൂപ്പർ ഗ്രൂപ്പിന്റെയും ചാനലിന്റെയും ലിങ്ക് മാത്രേ തരാൻ പറ്റു സോറി😞!")


@run_async
def adminlist(bot: Bot, update: Update):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = "[{}](tg://user?id={})".format(user.first_name + " " + (user.last_name or ""), user.id)
        if user.username:
            name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if status == "creator":
            text += "\n 🔱 Creator:"
            text += "\n` • `{} \n\n 🔰 Admin:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = "[{}](tg://user?id={})".format(user.first_name + " " + (user.last_name or ""), user.id)
        if user.username:
            name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if status == "administrator":
            text += "\n` • `{}".format(name)
    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))


__help__ = """
 - /adminlist: ചാറ്റിലെ അഡ്മിൻമാരുടെ പട്ടിക..

*Admin only:*
 - /pin: ഉപയോക്താക്കൾക്ക് അറിയിപ്പുകൾ നൽകുന്നതിന് 'ഉച്ചത്തിൽ' അല്ലെങ്കിൽ 'അറിയിക്കുക' എന്നതിന് മറുപടി നൽകിയ സന്ദേശം നിശബ്ദമായി പിൻ ചെയ്യുന്നു.
 - /unpin: നിലവിൽ പിൻ ചെയ്ത സന്ദേശം അൺപിൻ ചെയ്യുന്നു
 - /invitelink: invitelink ലഭിക്കുന്നു
 - /promote: മറുപടി നൽകിയ ഉപയോക്താവിനെ പ്രോത്സാഹിപ്പിക്കുന്നു
 - /demote: ഉപയോക്താവ് മറുപടി നൽകിയ ഡെമോട്ട് ചെയ്യുന്നു
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = CommandHandler("invitelink", invite, filters=Filters.group)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True, filters=Filters.group)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True, filters=Filters.group)

ADMINLIST_HANDLER = DisableAbleCommandHandler("adminlist", adminlist, filters=Filters.group)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
