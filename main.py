import json
from utils import *
current_block = GetCurrentBlock()
response = GetAllLogsByTopicInChunks(current_block-100000,'0x2e1f85a64a2f22cf2f0c42584e7c919ed4abe8d53675cff0f62bf1e95a1c676f')
print(response)