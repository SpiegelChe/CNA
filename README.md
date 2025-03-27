# CNA HTTP Web Proxy Server
---
### Start proxy server
    python <directory\filename> <IPaddr> <portnum>

### I. Test HTTP Status Code 200
    1. curl -iS http://localhost:8080/http://http.badssl.com/
    2. telnet localhost 8080
          GET http://http.badssl.com/ HTTP/1.1

### II. Test cache:
    running 'curl' or 'telnet' for the second time, trigger 'Cache hit! Loading from cache file: '

### III. Test HTTP Status Code 301 & 302
    1.1 curl -iS "http://localhost:8080/http://httpbin.org/redirect-to?url=http://http.badssl.com&status_code=301"
    1.2 curl -iS "http://localhost:8080/http://httpbin.org/redirect-to?url=http://http.badssl.com&status_code=302"
    2 telnet localhost 8080
        2.1 GET http://httpbin.org/redirect-to?url=http://http.badssl.com&status_code=301 HTTP/1.1
        2.2 GET http://localhost:8080/http://httpbin.org/redirect-to?url=http://http.badssl.com&status_code=302 HTTP/1.1

### IV. Test HTTP Status Code 404
    1. curl -iS http://localhost:8080/http://http.badssl.com/fakefile.html
    2. telnet localhost 8080
          GET http://http.badssl.com/fakefile.html HTTP/1.1

### V. Test cache-control header 'max-age=<seconds>'
    1.1 curl -iS "http://localhost:8080/http://httpbin.org/cache/0"
    1.2 curl -iS "http://localhost:8080/http://httpbin.org/cache/3600"
    2 telnet localhost 8080
        2.1 GET http://httpbin.org/cache/0 HTTP/1.1
        2.2 GET http://httpbin.org/cache/3600 HTTP/1.1
    


        
