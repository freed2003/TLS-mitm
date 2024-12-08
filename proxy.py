import socket
import threading
import ssl
import sys, os


HOST = "127.0.0.1"  # Localhost
PORT = 8443         # Port to listen on
LOG_FILE = "requests.log"  # File to save incoming requests
CERT_FILE = "cert.pem"  # Path to your SSL certificate
KEY_FILE = "key.pem" 
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)  # Listen for up to 5 connections
        print(f"HTTPS Proxy running on {HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Incoming connection from {client_address}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()

def handle_client(client_socket):
    try:
        # Read the initial HTTP request from the client
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Received request:\n{request}")

        # Parse the CONNECT request
        request_lines = request.split("\r\n")
        connect_line = request_lines[0].split()
        if len(connect_line) < 3 or connect_line[0].upper() != "CONNECT":
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            return

        target_host, target_port = connect_line[1].split(":")
        target_port = int(target_port)

        # Establish connection to the target server
        with socket.create_connection((target_host, target_port)) as target_socket:
            # Notify the client that the tunnel is established
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            # Log the request
            # with open(LOG_FILE, "a") as f:
            #     f.write(request + "\n")

            # Relay traffic between client and target server
            relay_traffic(client_socket, target_socket, target_host)
    except Exception as e:
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print(exc_type, fname, exc_tb.tb_lineno)
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def relay_traffic(client_sock, target_sock, target_hostname):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    ssl_sock = context.wrap_socket(client_sock, server_side=True)
    target_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    targt_ssl = target_context.wrap_socket(target_sock, server_hostname=target_hostname)

    def forward(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                with open(LOG_FILE, "ab") as f:
                    f.write(data + b"\r\n\r\n")
                dst.sendall(data)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        finally:
            src.close()
            dst.close()

    client_to_target = threading.Thread(target=forward, args=(ssl_sock, targt_ssl))
    target_to_client = threading.Thread(target=forward, args=(targt_ssl, ssl_sock))
    client_to_target.start()
    target_to_client.start()
    client_to_target.join()
    target_to_client.join()

if __name__ == "__main__":
    start_server()
