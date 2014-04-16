from gevent import monkey; monkey.patch_all()
import socket
import threading
import unittest


class Test(unittest.TestCase):

    def assert_closed(self, sock):
        try:
            result = sock.getsockname()
        except IOError, ex:
            if ex.errno == 9:
                return True
            raise
        raise AssertionError('%r.getsockname() returned %r' % (sock, result))

    def assert_not_closed(self, sock):
        result = sock.getsockname()
        assert isinstance(result, tuple), result


class TestSocket(Test):

    def test_simple_close(self):
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        self.assert_not_closed(s)
        s.close()
        self.assert_closed(s)

    def test_makefile1(self):
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        self.assert_not_closed(s)
        f = s.makefile()
        self.assert_not_closed(s)
        s.close()
        # closing underlying socket does close it
        self.assert_closed(s)
        f.close()
        self.assert_closed(s)

    def test_makefile2(self):
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        self.assert_not_closed(s)
        f = s.makefile()
        self.assert_not_closed(s)
        f.close()
        # closing fileobject does not close the socket
        self.assert_not_closed(s)
        s.close()
        self.assert_closed(s)

    def test_server_simple(self):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        listener.listen(1)

        connector = socket.socket()

        def connect():
            connector.connect(('127.0.0.1', port))

        threading.Thread(target=connect).start()
 
        client_socket, _addr = listener.accept()
        self.assert_not_closed(client_socket)
        client_socket.close()
        self.assert_closed(client_socket)

    def test_server_makefile1(self):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        listener.listen(1)

        connector = socket.socket()

        def connect():
            connector.connect(('127.0.0.1', port))

        threading.Thread(target=connect).start()
 
        client_socket, _addr = listener.accept()
        f = client_socket.makefile()
        self.assert_not_closed(client_socket)
        # closing underlying socket also closes fileobject
        client_socket.close()
        self.assert_closed(client_socket)
        f.close()
        self.assert_closed(client_socket)

    def test_server_makefile2(self):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        listener.listen(1)

        connector = socket.socket()

        def connect():
            connector.connect(('127.0.0.1', port))

        threading.Thread(target=connect).start()
 
        client_socket, _addr = listener.accept()
        f = client_socket.makefile()
        self.assert_not_closed(client_socket)
        # closing fileobject does not close the socket
        f.close()
        self.assert_not_closed(client_socket)
        client_socket.close()
        self.assert_closed(client_socket)


if __name__ == '__main__':
    unittest.main()
