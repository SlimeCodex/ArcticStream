import socket
import select
import errno
import time

def main():
	host = '192.168.0.5'  # Replace with your ESP32's IP address
	port = 56320  # Port number should match the one on the ESP32 server

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setblocking(False)

	try:
		s.connect((host, port))
	except socket.error as err:
		if err.errno != errno.WSAEWOULDBLOCK:
			print(f"Connection failed: {err}")
			return

	# Wait for the socket to be ready
	ready_to_read, ready_to_write, in_error = select.select([], [s], [], 5)

	if ready_to_write:
		print("Connection established")

		data_buffer = b""  # Initialize a buffer for incoming data

		# Now receive data
		while True:
			try:
				data = s.recv(1024)  # Increased buffer size
				if data:
					data_buffer += data
					while b'\n' in data_buffer:
						# Split the buffer at the newline and print the first part if not empty
						line, data_buffer = data_buffer.split(b'\n', 1)
						line = line.strip()  # Remove leading and trailing whitespaces
						if line:  # Check if line is not empty
							print(line.decode())
				else:
					print("Connection closed by the server")
					break
			except socket.error as e:
				if e.errno != errno.WSAEWOULDBLOCK:
					print("Socket error:", e)
					break
				else:
					time.sleep(0.01)
					continue

	else:
		print("Connection failed: Timeout or error")

	s.close()

if __name__ == "__main__":
	main()