import sys
import json

with open('settings.json','r') as f:
    data = json.load(f)
    this = sys.modules[__name__]
    for k,v in data.items():
        setattr(this, k, v)
