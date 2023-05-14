from classes import *
import json
from utils import *
current_block = GetCurrentBlock()
response = GetAllLogsByTopicInChunks(current_block-100000,'0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022')
print(response[len(response)-1])

