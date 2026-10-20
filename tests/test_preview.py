"""The native media player needs real byte-range responses for chapter seeking."""
import sys,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from serve import Handler
class Ranges(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
  cls.url=f'http://127.0.0.1:{cls.server.server_port}/media/circles.mp4'
  cls.size=(ROOT/'site/media/circles.mp4').stat().st_size
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def test_initial_probe(self):
  with urllib.request.urlopen(urllib.request.Request(self.url,headers={'Range':'bytes=0-1'})) as r:
   self.assertEqual(r.status,206);self.assertEqual(r.headers['Content-Range'],f'bytes 0-1/{self.size}');self.assertEqual(len(r.read()),2)
 def test_suffix(self):
  with urllib.request.urlopen(urllib.request.Request(self.url,headers={'Range':'bytes=-8'})) as r:
   self.assertEqual(r.status,206);self.assertEqual(len(r.read()),8)
 def test_out_of_bounds(self):
  with self.assertRaises(urllib.error.HTTPError) as e:
   urllib.request.urlopen(urllib.request.Request(self.url,headers={'Range':f'bytes={self.size}-'}))
  self.assertEqual(e.exception.code,416)
  e.exception.close()
if __name__=='__main__':unittest.main()
