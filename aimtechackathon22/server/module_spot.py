from module import HackathonModule

from keras.models import Sequential, load_model, save_model
from keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from sentence_transformers import SentenceTransformer
from os.path import isfile
from requests import post
from json import dumps
import numpy as np


MODULE_NAME = 'Spot'

MOVES = {
    1: 'Doleva',
    2: 'Doprava',
    3: 'Nahoru',
    4: 'Sedni',
    5: 'Lehni'
}

# Model params
N = 768
H = [15, 10]
EPOCHS = 250
BS = 1

# SBert
SBERT = SentenceTransformer('bert-base-nli-mean-tokens')

# Pre-trained model
USE_MODEL = False
MODEL = f'models/hack/{MODULE_NAME}.h5'

# Robot control
CMD_BASE = 'http://localhost:7001/spot/'
ONLINE = True


class AimtecBot(HackathonModule):

    def __init__(self):
        HackathonModule.__init__(self, name=MODULE_NAME)

        self.moves = MOVES

        # EXPERIENCE
        self.exp_x = []
        self.exp_y = []

        # ENCODING - BERT
        self.encodings = {}

        # NET
        if USE_MODEL and isfile(MODEL):
            self.net = load_model(MODEL)
        else:
            self.net = self.design_net(last=False)

    def design_net(self, last=False, do_compile=True):
        net = Sequential()
        net.add(Dense(H[0], input_dim=N, batch_size=1, activation='sigmoid'))
        for h in H[1:]:
            net.add(Dense(h, activation='sigmoid'))
        
        net.add(Dense(len(MOVES), activation='sigmoid'))

        if last:
            rl_layer = Dense(1, activation='sigmoid')
            rl_layer.trainable = False
            rl_layer.set_weights(0.1*np.ones(shape=len(rl_layer.get_weights())))
            net.add(rl_layer)
        
        if do_compile:
            opt = Adam(learning_rate=0.0001)
            net.compile(loss='mse', optimizer=opt, metrics=['categorical_accuracy'])
        
        print('NET designed.', net.summary())
        return net

    def encode(self, text):
        if text not in self.encodings:
            self.encodings[text] = SBERT.encode([text])[0]
        
        return np.array(self.encodings[text], ndmin=2)

    def decode(self, vec):
        move_ind = np.argmax(vec)+1
        move = MOVES[move_ind]
        return move

    def make_move(self, move):
        body = {
            'command': move
        }
        _ = post(CMD_BASE, dumps(body)).json()['answer']

    def react(self, text):
        if 'stop' in text.lower():
            self.make_move('Lehni')
            return 'Zastavuji.', np.array([])

        inp = self.encode(text)
        vector = self.net.predict(inp)[0]
        self.last_out = vector
        move = self.decode(vector)
        
        self.make_move(move)

        return move, vector

    def retrain(self):
        X = np.array(self.exp_x, ndmin=2).squeeze(1)
        Y = np.array(self.exp_y, ndmin=2)

        history = self.net.fit(X, Y, epochs=EPOCHS, batch_size=BS, verbose=False)
        current_acc = history.history['categorical_accuracy'][-1]
        current_loss = history.history['loss'][-1]
        print(f'Retrained. Acc: {current_acc} / Loss: {current_loss}')

        if MODEL and USE_MODEL:
            save_model(self.net, MODEL)
            print(f'Model saved to {MODEL}')

    def prompt(self, text):
        self._prompt(text)
        answer, vector = self.react(text)
        
        return answer, vector

    def encode_feedback(self, text):
        if text == 'ok':
            ind = np.argmax(self.last_out)
            ret = np.zeros(shape=len(MOVES))
            ret[ind] = 1.
            return ret
        elif text == 'no':
            ind = np.argmax(self.last_out)
            ret = 0.5*np.ones(shape=len(MOVES))
            ret[ind] = 0.
            return ret
        elif False:
            pass
            #add numerical values here #TODO

    def feedback(self, text):
        self.exp_x.append(self.encode(self.last_prompt))
        self.exp_y.append(self.encode_feedback(text))

        print(f'Already have {len(self.exp_x)} hints. Retraining...')

        self.retrain()

        return text
