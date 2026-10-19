#!/usr/bin/env python3
"""Local static preview with byte ranges for video seeking (no production backend)."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import argparse,re,shutil
SITE=Path(__file__).resolve().parents[1]/'site'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(SITE),**kwargs)
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes');self.send_header('Cache-Control','no-cache');super().end_headers()
    def send_head(self):
        self.remaining=None;path=Path(self.translate_path(self.path));header=self.headers.get('Range')
        if not header or not path.is_file():return super().send_head()
        size=path.stat().st_size;m=re.fullmatch(r'bytes=(\d*)-(\d*)',header)
        if not m or not any(m.groups()):self.send_error(416,'Invalid range');return None
        if m[1]:start=int(m[1]);end=min(size-1,int(m[2]) if m[2] else size-1)
        else:start=max(0,size-int(m[2]));end=size-1
        if start>=size or end<start:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
        f=path.open('rb');f.seek(start);self.remaining=end-start+1
        self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(self.remaining));self.end_headers();return f
    def copyfile(self,source,outputfile):
        if self.remaining is None:return shutil.copyfileobj(source,outputfile)
        while self.remaining:
            chunk=source.read(min(self.remaining,64*1024))
            if not chunk:break
            outputfile.write(chunk);self.remaining-=len(chunk)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8785);a=p.parse_args()
    print(f'Local: http://127.0.0.1:{a.port}/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
