# https://www.linuxtut.com/en/53348de9d1dd4fde4a00/
import http.server
import socketserver
import os
import re
import urllib
import sys
import json

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

RANGE_BYTES_RE = re.compile(r'bytes=(\d*)-(\d*)?\Z')
BUFSIZE = 16 * 1024
EXTENSIONS = ['m4v', 'mp4', 'avi']

def gather_videos(path):
    videos = []
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(path):
        videos = videos + [f'{path}/{file}' for file in files if any([file.endswith(ext) for ext in EXTENSIONS])]

    return videos

videos_path_g='/videos'
def get_videos(self):
  videos = gather_videos(videos_path_g);
  self.send_response(200)
  self.send_header('Content-type', 'application/json')
  self.end_headers()
  self.wfile.write(bytes(json.dumps(videos), 'utf-8'))

methods = {
    '/videos': get_videos,
}

class RangeRequestNoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in methods:
            return methods[self.path](self)
        else:
          return http.server.SimpleHTTPRequestHandler.do_GET(self)

    # overriding
    def send_head(self):
        if 'Range' not in self.headers:
            self.range = None
            return super().send_head()
        try:
            self.range = self._parse_range_bytes(self.headers['Range'])
        except ValueError as e:
            self.send_error(416, 'Requested Range Not Satisfiable')
            return None
        start, end = self.range

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            print(parts)
            if not parts.path.endswith('/'):
                self.send_response(301)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break

        f = None
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, 'Not Found')
            return None

        self.send_response(206)

        ctype = self.guess_type(path)
        self.send_header('Content-type', ctype)
        self.send_header('Accept-Ranges', 'bytes')

        fs = os.fstat(f.fileno())
        file_len = fs[6]
        if start != None and start >= file_len:
            self.send_error(416, 'Requested Range Not Satisfiable')
            return None
        if end == None or end > file_len:
            end = file_len

        self.send_header('Content-Range', 'bytes %s-%s/%s' % (start, end - 1, file_len))
        self.send_header('Content-Length', str(end - start))
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def _parse_range_bytes(self, range_bytes):
        if range_bytes == '':
            return None, None

        m = RANGE_BYTES_RE.match(range_bytes)
        if not m:
            raise ValueError('Invalid byte range %s' % range_bytes)

        if m.group(1) == '':
            start = None
        else:
            start = int(m.group(1))
        if m.group(2) == '':
            end = None
        else:
            end = int(m.group(2)) + 1

        return start, end

    # overriding
    def end_headers(self):
        #Code to disable the browser cache
        self.send_header('Cache-Control', 'max-age=0')
        self.send_header('Expires', '0')
        super().end_headers()

    # overriding
    def copyfile(self, source, outputfile):
        try:
            if not self.range:
                return super().copyfile(source, outputfile)

            start, end = self.range
            self._copy_range(source, outputfile, start, end)
        except BrokenPipeError:
            #When you seek a video on your browser
            #The browser interrupts the response reception of the video file
            #Because this error will occur
            #Ignore this
            pass

    def _copy_range(self, infile, outfile, start, end):
        if start != None:
            infile.seek(start)
        while True:
            size = BUFSIZE
            if end != None:
                left = end - infile.tell()
                if left < size:
                    size = left
            buf = infile.read(size)
            if not buf:
                break
            outfile.write(buf)

def get_args(argv):
    if len(argv) == 4:
      try:
        return [argv[1], int(argv[2]), argv[3]]
      except ValueError:
        return ['localhost', 8000, '/videos']
    print(f'incorrect number of arg ({len(argv)} instead of 3)')
    return ['localhost', 8000, '/videos']

def main(argv):
    global videos_path_g

    addr = 'localhost'
    [addr, port, videos_path] = get_args(argv)
    videos = gather_videos(videos_path)
    videos_path_g = videos_path

    print(f'Serving {len(videos)} videos from {videos_path} on {addr} port {port} (http://{addr}:{port}) ...');
    httpServer = ThreadingHTTPServer((addr, port), RangeRequestNoCacheHTTPRequestHandler)
    httpServer.serve_forever()

if __name__ == '__main__':
  main(sys.argv)

