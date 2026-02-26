import re

def escape_md(text: str) -> str:
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(special_chars), r'\\\1', text)