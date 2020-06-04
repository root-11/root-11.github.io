from flask import Flask


server = None


class TestServer(object):
    def __init__(self):
        self._app = Flask(__name__)
        self._app.add_url_rule(rule='/', view_func=self.index, methods=['GET'])
        self._app.add_url_rule(rule='/hello/<string:name>', view_func=self.hello, methods=['POST'])

    def index(self):
        return "Hello from index"

    def hello(self, name):
        return f"Hello {name} from index"


class Client(object):
    server = None
    client = None

    @classmethod
    def setup(cls, server):
        cls.server = server
        cls.client = server._app.test_client()

    def get(self, url, *args, **kwargs):
        return self.client.get(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.client.post(url, *args, **kwargs)


def setup():
    global server
    server = TestServer()
    Client.setup(server)


def teardown():
    pass


def test_hello():
    client = Client()
    reply = client.get('/')
    assert "Hello" in reply.data.decode()


def test_hello_me():
    client = Client()
    reply = client.post('/hello/me')
    assert "me" in reply.data.decode()


def run():
    setup()
    for k,v in sorted(globals().items()):
        if callable(v) and k.startswith('test'):
            v()
    teardown()

run()