import json


class JSONSerializer:
    def dumps(self, value):
        return json.dumps(value)

    def loads(self, value):
        if value is None:
            return None
        return json.loads(value)
