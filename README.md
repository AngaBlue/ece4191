# Engineering Integrated Design (ECE4191) - R06
## Project Structure
### `/firmware`
Contains the C++ firmware to be uploaded to the ESP32.  In order to activate the Platform.IO open VSCode to the `/firmware` directory rather than the root directory.

### `/scripts`
Contains Python scripts primarily used for debugging and Machine Learning training.

### `/ui`
A demo UI with a low-latency video stream, controller inputs and commands sending.

## Contribution
The `main` branch of this repository is protected, meaning that in order to push code to main, you will first need to do so via a pull request (PR).  To get started, create a branch off main with a meaningful name:

```sh
git checkout -b <branch_name>
```
*Change `<branch_name>` to be the name of your branch.*

You can keep pushing to this branch while you are working.  When the feature is done, please create a PR to have it reviewed before merging to main.  Test that your code works before creating a PR.

## Connecting
Start a local hotspot on Windows by opening `Settings > Network & internet > Mobile hotspot`.
 - Share over: `WiFi`
 - Network Properties:
   - Any name and password, just remember to white the same name later.
   - Network band: `2.4GHz`

Start the mobile hotspot.  This will allow you to stay connected to the internet while controlling the robot.

To program the robot to use your hotspot, open `/firmware/include/config.h` and modify `HOTSPOT_SSID` and `HOTSPOT_PASS` to match your Network Properties.  Once set, build and upload the code (more instructions on this process can be found in `/firmware/README.md`).

As the MCU may be assigned a new IP on each connection, use the `get_ip()` function from `/ui/ip.py` to programmatically find the IP of the MCU on startup.

## Low-Latency Frame Video Feed
In order to reduce the video feed latency frames are served as 640x480 MJPEG on RTSP over UDP.  On both the MCU and client, the frame buffer should be a single frame in order to only serve the most recent information, at the cost of frame pacing.  A frame bus is provided in `/ui/FrameBus.py` to simplify reading the video stream, with example usage found in `/ui/app.py`.

While the below command is provided to view the RTSP stream, it suggested that you instead run the `/ui/app.py` script as this will automatically find the IP.

```bash
ffplay -rtsp_transport udp -probesize 32 -analyzeduration 0 -vf setpts=0 -vcodec mjpeg -acodec pcm_s16be -ar 48000 -fflags nobuffer -fflags discardcorrupt -flags low_delay -framedrop rtsp://IP/
```

You will need FFMPEG installed, which can be done by running `winget install ffmpeg`.

## Operation Commands
Once again, to reduce latency, commands are sent as single packets over UDP.  This does mean that commands may be dropped if the connection is poor.  Each command is variable length set of packed bytes in the following format:

```
[CMD:1][LEN:1][ID:1][PAY:LEN][CHK:1]
```

This yields a 3 byte header, variable length payload and a 1 byte checksum.  Functions are provided in `/ui/commands.py` to simplify sending these commands to the MCU.

It is expected the the remote client device should be continually sending commands to the MCU, even if they have not changed.  If no inputs are received after a configurable amount of time, the MCU will assume a connection issue and pause all motor movement.
