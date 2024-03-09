    
    
class ChatModel:
    
    def __init__(self, **config):
        self.__dict__.update(**config)

    def turn(self, prompt):
        ## -- TODO
        reaction = f'Reaction to {prompt}'

        return reaction
