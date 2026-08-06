import logging
import os

logger = logging.getLogger(__name__)


def notify_whatsapp(phone: str, text: str) -> None:
    """Stub WhatsApp: no-op/log unless WHATSAPP_ENABLED=1."""
    if not phone:
        return
    if os.environ.get('WHATSAPP_ENABLED') != '1':
        logger.debug('WhatsApp disabled: to=%s text=%s', phone, text[:80])
        return
    # ponytail: no provider wired; ceiling = real API (Evolution/Meta). Upgrade: call provider here.
    logger.info('WhatsApp stub send to=%s text=%s', phone, text[:200])
