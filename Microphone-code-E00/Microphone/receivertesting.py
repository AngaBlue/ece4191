import socket
import numpy as np
import time
from scipy.io.wavfile import write
# Configuration
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 12345    # Port to listen on

def normalize_audio(audio_data):
    """Normalize audio to use full dynamic range"""
    # Convert to float for processing
    audio_float = audio_data.astype(np.float64)
    
    # Find the maximum absolute value
    max_val = np.max(np.abs(audio_float))
    
    if max_val > 0:  # Avoid division by zero
        # Normalize to use full scale
        normalized = audio_float / max_val
        # Convert back to 16-bit integers
        return (normalized * 32767).astype(np.int16)
    else:
        return audio_data

# Create the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(1.0)  # Timeout after 1 second (adjust as needed)

print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")
allData = np.array([])

startTime = time.time()
try:
    while True:
        try:
            # Try to receive data
            data, addr = sock.recvfrom(1024)
            decoded = np.frombuffer(data, dtype='<i2')
            # print(f"Received message: {decoded} from {addr}")
            allData = np.append(allData, decoded)
            #print(allData)
        except socket.timeout:
            # No data received during timeout window; loop continues
            continue
except KeyboardInterrupt:
    print("\nExiting due to KeyboardInterrupt...")
    endTime = time.time()
    samPSec = int(np.floor(len(allData)/(endTime-startTime)))
    print("Samples per second",samPSec)
    #write("c:/Users/kunal/Documents/Arduino/example.wav", 44100, allData.astype(np.int16))
    if len(allData) > 0:
        normalized_data = normalize_audio(allData.astype(np.int16))
        write("c:/Users/kunal/Documents/Arduino/example.wav", 44100, normalized_data)
        print("Audio normalized and saved")
    else:
        print("No data received")
finally:
    sock.close()