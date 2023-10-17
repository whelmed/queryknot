# QueryKnot: A Lightweight Data Format for Linking LLM Queries with Application Logic

JSON, YAML, TOML, etc., are ubiquitous data formats. However, using Large Language Models (LLMs) to produce these formats can be slow and consume a substantial number of tokens. Models that generate JSON require additional training and currently incur higher operational costs. Moreover, not all LLMs can effortlessly produce JSON.

The primary goal of QueryKnot is to offer a lightweight format that is easy to parse and generate. This format can be effortlessly converted into other formats or translated into objects in various programming languages.

QueryKnot utilizes a key-value format that flattens objects into a single level. Keys are represented as dot-separated strings, while values can be strings, numbers, booleans, or collections. Please note that nested collections are not supported.

**Example Format:**

```plaintext
user.name "Cansu"
user.age 25
user.location "Istanbul"
conversation.topics ["politics" "sports" "technology"]
```

**Example Usage:**

```python
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
# Displays something similar to: topics ["chocolate chip cookies" "bread" "bread maker"]
print(extracted_topics)
# Produces an object with a topics attribute
topics = parse_into_object(extracted_topics)
# Produces a dict with content similar to: {'topics': ['chocolate chip cookies', 'bread', 'bread maker']}
topics = parse_into_dict(extracted_topics)
```
