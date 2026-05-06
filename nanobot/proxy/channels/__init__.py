"""Proxy channels - each runs as a separate process."""

from nanobot.proxy.channels.dingtalk import DingTalkProxyChannel
from nanobot.proxy.channels.discord import DiscordProxyChannel
from nanobot.proxy.channels.email import EmailProxyChannel
from nanobot.proxy.channels.feishu import FeishuProxyChannel
from nanobot.proxy.channels.matrix import MatrixProxyChannel
from nanobot.proxy.channels.mochat import MochatProxyChannel
from nanobot.proxy.channels.msteams import MSTeamsProxyChannel
from nanobot.proxy.channels.qq import QQProxyChannel
from nanobot.proxy.channels.slack import SlackProxyChannel
from nanobot.proxy.channels.telegram import TelegramProxyChannel
from nanobot.proxy.channels.weixin import WeixinProxyChannel
from nanobot.proxy.channels.wecom import WecomProxyChannel
from nanobot.proxy.channels.whatsapp import WhatsAppProxyChannel

__all__ = [
    "FeishuProxyChannel",
    "DingTalkProxyChannel",
    "WecomProxyChannel",
    "DiscordProxyChannel",
    "SlackProxyChannel",
    "QQProxyChannel",
    "TelegramProxyChannel",
    "WhatsAppProxyChannel",
    "MatrixProxyChannel",
    "WeixinProxyChannel",
    "MochatProxyChannel",
    "MSTeamsProxyChannel",
    "EmailProxyChannel",
]