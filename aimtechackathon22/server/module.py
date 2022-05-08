

class HackathonModule:

    def __init__(self, name):
        self.name = name
        self.last_prompt = ''
        self.last_out = None

    def _prompt(self, text):
        self.last_prompt = text