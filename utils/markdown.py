def escape_md(text):

    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']


    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text