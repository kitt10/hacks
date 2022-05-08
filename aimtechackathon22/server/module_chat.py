from module import HackathonModule
from transformers import T5Tokenizer, TFT5ForConditionalGeneration
from time import time
import tensorflow as tf

MODULE_NAME = 'AimtecHackathon - Chat'

MODEL_PATH = 'models/m1'
TOKENIZER_PATH = 'models/tokenizer.model'


class Chat(HackathonModule):

    def __init__(self):
        HackathonModule.__init__(self, name=MODULE_NAME)
        self.model_fn = MODEL_PATH
        self.tokenizer_fn = TOKENIZER_PATH
        self.tokenizer = None
        self.load_tokenizer()
        self.model = None
        self.load_model()

    def load_tokenizer(self):
        self.tokenizer = T5Tokenizer(self.tokenizer_fn)
        print(f'Tokenizer from {self.tokenizer_fn} loaded.')

    def load_model(self):
        self.model = TFT5ForConditionalGeneration.from_pretrained(self.model_fn)
        print(f'Model from {self.model_fn} loaded.')

    def predict(self, sentence):
        t0 = time()
        sentences = self.tokenizer([sentence])
        input_ids = tf.constant(sentences["input_ids"])
        outputs = self.model.generate(input_ids)
        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        t = time()-t0

        print('DIA LOG:', sentence, '->', answer)
        print('DIA LOG: Inference time:', round(t, 4), 'seconds')

        return answer

    def prompt(self, text):
        self._prompt(text)
        return self.predict(sentence=text)