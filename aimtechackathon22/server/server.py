from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.ioloop import IOLoop
from tornado.escape import json_decode
from os.path import join, dirname
from json import dump as dump_json, load as load_json
from datetime import datetime

# MODULES
from module_chat import Chat
from module_aimtecbot import AimtecBot
#from module_spot import Spot


class EP_Web(RequestHandler):

    def initialize(self, path):
        self.path = path

    def get(self):
        self.render(join(self.path, 'index.html'))
        
class EP_WebPage(RequestHandler):

    def initialize(self, path):
        self.path = path

    def get(self, page):
        pages = ['readme']
        if page in pages:
            self.render(join(self.path, page+'.html'))
        else:
            self.render(join(self.path, 'index.html'))

class EP_Dialog(RequestHandler):

    def initialize(self, webserver, worker):
        self.webserver = webserver
        self.worker = worker

    def post(self):
        query = json_decode(self.request.body)
        if 'message' in query:
            message = query['message']
            self.webserver.log('[LOG]: New message: '+str(message))
            answer = self.worker.session(text=message)
            self.write({'answer': answer})
        elif 'feedback' in query:
            feedback = query['feedback']
            device = query['device']
            self.webserver.log('[LOG]: New feedback: '+str(feedback))
            self.worker.feedback(text=feedback, device=device)
            self.write({'answer': 'OK, díky.'})
        else:
            self.webserver.log('[LOG]: Unknown query: '+str(query))
        
    def options(self):
        self.set_status(204)
        self.finish()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Request-Headers", "Content-Type")
           
class WebServer:
    
    def __init__(self, worker, port, rel_static_path, verbose):
        self.worker = worker
        self.port = port
        self.rel_static_path = rel_static_path
        self.static_path = join(dirname(__file__), self.rel_static_path)
        self.verbose = verbose
        
        urls = [('/', EP_Web, {'path': self.static_path}),
                (r'/([a-z]+)', EP_WebPage, {'path': self.static_path}),
                ('/dialog/', EP_Dialog, {'webserver': self, 'worker': self.worker}),
                ('/(.*)', StaticFileHandler, {'path': self.static_path})]

        settings = {
                'debug': True, 
                'autoreload': True}

        app = Application(urls, **settings)
        app.listen(self.port)

        self.log('Starting server, port: '+str(self.port))
        IOLoop.current().start()

    def log(self, buf):
        if self.verbose:
            print('SERVER LOG:', buf)
                 
class Worker:
    
    def __init__(self, base_static_path, module):
        self.base_static_path = base_static_path
        self.module = module
        self.last_ts = ''

        # default data
        default_data = {
            "dialog": {
                    "prompt": "", 
                    "answer": "", 
                    "vector": []
                }, 
            "feedback": {}, 
            "moves": self.module.moves,
            "name": self.module.name,
            "ts": ""
        }
        
        with open(join(self.base_static_path, 'data', 'data.json'), 'w', encoding='utf-8') as fwj:
            dump_json(default_data, fwj)

    def session(self, text):
        answer, vector = self.module.prompt(text)
        self.dialog_to_gui(text, answer, vector)
        return answer

    def feedback(self, text, device):
        feedback = self.module.feedback(text)
        self.feedback_to_gui(feedback, device)

    def dialog_to_gui(self, prompt, answer, vector):
        with open(join(self.base_static_path, 'data', 'data.json'), 'r', encoding='utf-8') as frj:
            data = load_json(frj)
        
        self.last_ts = datetime.now().strftime("%H:%M:%S")
        data['dialog']['prompt'] = prompt
        data['dialog']['answer'] = answer
        data['dialog']['vector'] = vector.tolist()
        data['ts'] = self.last_ts

        with open(join(self.base_static_path, 'data', 'data.json'), 'w', encoding='utf-8') as fwj:
            dump_json(data, fwj)
    
    def feedback_to_gui(self, feedback, device):
        with open(join(self.base_static_path, 'data', 'data.json'), 'r', encoding='utf-8') as frj:
            data = load_json(frj)

        data['feedback'][self.last_ts] = {
            'val': 1 if feedback == 'ok' else 0,
            'device': device
        }

        with open(join(self.base_static_path, 'data', 'data.json'), 'w', encoding='utf-8') as fwj:
            dump_json(data, fwj)
    

if __name__ == '__main__':

    SERVER_PORT = 7000
    RELATIVE_STATIC_PATH = './gui/deploy'

    # Define your module here
    #MODULE = Chat()
    MODULE = AimtecBot()
    #MODULE = Spot()
    
    worker = Worker(base_static_path=RELATIVE_STATIC_PATH, module=MODULE)

    # Init and Run WebServer
    WebServer(worker=worker,
              port=SERVER_PORT, 
              rel_static_path=RELATIVE_STATIC_PATH, 
              verbose=True)
