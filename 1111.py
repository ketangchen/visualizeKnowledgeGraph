# -*- coding: utf-8 -*-
import os
import openai

# optional; defaults to `os.environ['OPENAI_API_KEY']`
openai.api_key = "sk-jaRSXNMxl1xdjOzu5e8e780c79Ee40D99aE43c0b74A90fF6"

# all client options can be configured just like the `OpenAI` instantiation counterpart
openai.base_url = "https://free.v36.cm/v1/"
openai.default_headers = {"x-foo": "true"}

completion = openai.chat.completions.create(
    model="gpt-4o-mini", ##gpt-4o-mini,gpt-3.5-turbo
    messages=[
        {
            "role": "user",
            "content": "请解释下什么是软件工程？",
        },
    ],
)
print(completion.choices[0].message.content)


# /usr/local/bin/python3.7 -m pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple

