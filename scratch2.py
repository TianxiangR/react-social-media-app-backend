import re

pattern = r'^#(\b[A-Za-z][A-Za-z0-9]*\b)$'

text = 'This is a #test\n\r#post #hashtags #test'
words = text.split()
for word in words:
    match = re.match(pattern, word)
    if match:
        print(match.group(1))