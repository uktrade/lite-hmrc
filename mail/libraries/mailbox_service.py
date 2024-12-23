import logging
from typing import List, Optional

from mail.models import Mail

logger = logging.getLogger(__name__)


def find_mail_of(extract_types: List[str], reception_status: str) -> Optional[Mail]:
    try:
        mail = Mail.objects.get(status=reception_status, extract_type__in=extract_types)
    except Mail.DoesNotExist:
        logger.warning("Can not find any mail in [%s] of extract type [%s]", reception_status, extract_types)
        return

    logger.info("Found mail in [%s] of extract type [%s]", reception_status, extract_types)
    return mail
