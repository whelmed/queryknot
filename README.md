QueryKnot: a lightweight data format for tying LLM queries together with application logic.

JSON, YAML, TOML, etc are ubiquitous. However, having LLMs produce these formats is slow, and consumes a lot of tokens. 
Models that produce JSON require additional training, and currently cost more to run. Not all LLMs can easily produce JSON.

The goal of QueryKnot is to provide a lightweight format that is easy to parse, and easy to produce.

This format can be easily converted other formats, or into objects in a programming language.

QueryKnot is a key-value format that flattens objects into a single level.

Keys are dot separated strings, and values are strings, numbers, booleans, or collections.

Nested collections are not supported. 

Example format:

```
user.name "Cansu"
user.age 25
user.location "Istanbul"
conversation.topics ["politics" "sports" "technology"]
```


Example Usage:
```py
from queryknot import formatting_instructions, parse_into_dict, parse_into_object


theme = 'Baking'
convo = '''
Hey, how are you?
I'm good, how are you?
Good, just eating some vanilla ice cream.
Yum! I made some chocolate chip cookies earlier. 
You should crush them up and put them in your ice cream.
That sounds delicious.
I baked a lot of bread during quarantine.
I've been baking a lot of bread too. I've been shopping for a bread maker.
'''

query = '''
Overview:
    Extract discussed topics from the provided conversation related to a provided theme.

Example:
    Input: 
        theme: Programming
        conversation: 
            Hey, how are you?
            I'm good, how are you?
            Good, just eating some vanilla ice cream.
            Cool.
            I've been using Python to build AI-enabled apps.
            Neat.
            I've been playing a lot of video games lately.

    Output:
        topics: ["Python" "AI-enabled applications"]
    
Instructions:
    Extract only topics closely related to the theme.
    Omit the names of people involved or mentioned in the conversation.
                                        
Theme: {theme}

Example Output: topics ["topic1" "topic2" "topic3" ... "topicN"]

Formatting Instructions: {format_instructions}

Conversation: {conversation}

Output: 

'''.format(format_instructions=formatting_instructions(), conversation=convo, theme=theme)


extracted_topics = query_llm(query)
# Displays something similar too: topics ["chocolate chip cookies" "bread" "bread maker"]
print(extracted_topics)
# Produces an object with a topics attribute
topics = parse_into_object(extracted_topics)
# Produces a dict with content similar to: {'topics': ['chocolate chip cookies', 'bread', 'bread maker']}
topics = parse_into_dict(extracted_topics)

```
