# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  # Create a server socket
  # ~~~~ INSERT CODE ~~~~
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # ~~~~ END CODE INSERT ~~~~
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the the server socket to a host and port
  # ~~~~ INSERT CODE ~~~~
  serverSocket.bind((proxyHost, proxyPort))
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # ~~~~ INSERT CODE ~~~~
  serverSocket.listen(10)
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    # ~~~~ INSERT CODE ~~~~
    clientSocket, clientAddress = serverSocket.accept()
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes
  # ~~~~ INSERT CODE ~~~~
  message_bytes = b''
  clientSocket.settimeout(5.0)
  try:
    while True:
      data = clientSocket.recv(1)  # 1 byte is received at a time due to telnet sending 1 char at a time
      if not data:
        break
      message_bytes += data
      if message_bytes.endswith(b'\r\n\r\n'):  # end request when detecting empty line
        break
  except socket.timeout:
    print("Request timeout")
    clientSocket.close()
    continue
  # ~~~~ END CODE INSERT ~~~~
  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  if len(requestParts) < 3:  # end connection if wrong request format
    print("Invalid HTTP request format")
    print("Quitting...")
    clientSocket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
    clientSocket.close()
    break

  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)

    fileExists = os.path.isfile(cacheLocation)

    if fileExists:
      # Check whether the file is currently in the cache
      cacheFile = open(cacheLocation, "r")
      cacheData = cacheFile.readlines()

      print ('Cache hit! Loading from cache file: ' + cacheLocation)
      # ProxyServer finds a cache hit
      # Send back response to client
      # ~~~~ INSERT CODE ~~~~
      clientSocket.sendall(b''.join(cacheData))
      # ~~~~ END CODE INSERT ~~~~
      cacheFile.close()
      print ('Sent to the client:')
      print ('> ' + ''.join(cacheData))
    else:
      raise Exception("Cache miss")
  except:
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
    # ~~~~ INSERT CODE ~~~~
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerSocket.connect((address, 80))
      # ~~~~ END CODE INSERT ~~~~
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request
      # ~~~~ INSERT CODE ~~~~
      originServerRequest = f"{method} {resource} {version}"
      originServerRequestHeader = f"Host: {hostname}\r\nConnection: close\r\n"
      # ~~~~ END CODE INSERT ~~~~

      # Construct the request to send to the origin server
      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      # ~~~~ INSERT CODE ~~~~
      response = b''
      try:
        originServerSocket.settimeout(10)
        while True:
          data = originServerSocket.recv(BUFFER_SIZE)
          if not data:
            break
          response += data
          # Check if received full headers
          if b'\r\n\r\n' in response and (b'Content-Length:' in response or
                                          b'Transfer-Encoding: chunked' in response or
                                          response.startswith((b'HTTP/1.1 301', b'HTTP/1.1 302'))):
            break
      except socket.timeout:
        print("Origin server response timeout")
      # ~~~~ END CODE INSERT ~~~~

      # Handle redirects (301 and 302)
      if response.startswith(b'HTTP/1.1 301') or response.startswith(b'HTTP/1.1 302'):
        try:
          redirect_location = re.search(br'Location: (.*?)\r\n', response).group(1).decode('utf-8')
          print(f'Redirecting to: {redirect_location}')

          # Close existing connection
          originServerSocket.close()

          # Parse new location
          URI = redirect_location
          URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
          resourceParts = URI.split('/', 1)
          hostname = resourceParts[0]
          resource = '/' + resourceParts[1] if len(resourceParts) > 1 else '/'

          # Send redirect response to client
          clientSocket.sendall(response)
          clientSocket.close()
          continue
        except Exception as e:
          print(f'Redirect handling failed: {str(e)}')
          clientSocket.sendall(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
          clientSocket.close()
          continue

      # Handle Cache-Control header (max-age)
      cache_control = re.search(br'Cache-Control: max-age=(\d+)', response)
      if cache_control:
        max_age = int(cache_control.group(1))
        print(f'Cache-Control: max-age={max_age}')
        # Implement cache expiration logic here if needed

      # Send the response to the client
      # ~~~~ INSERT CODE ~~~~
      clientSocket.sendall(response)
      # ~~~~ END CODE INSERT ~~~~

      # Create a new file in the cache for the requested file.
      cacheDir, file = os.path.split(cacheLocation)
      print ('cached directory ' + cacheDir)
      if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
      cacheFile = open(cacheLocation, 'wb')

      # Save origin server response in the cache file
      # ~~~~ INSERT CODE ~~~~
      cacheFile.write(response)
      # ~~~~ END CODE INSERT ~~~~
      cacheFile.close()
      print ('cache file closed')

      # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
       
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')
