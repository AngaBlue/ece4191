# Engineering Integrated Design (ECE4191) - R06
## Project Structure
### `/firmware`
Contains the C++ firmware to be uploaded to the ESP32.  In order to activate the Platform.IO open VSCode to the `/firmware` directory rather than the root directory.

### `/scripts`
Contains Python scripts primarily used for debugging and Machine Learning training.

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

To program the robot to use your hotspot, open `/firmware/include/config.h` and modify `HOTSPOT_SSID` and `HOTSPOT_PASS` to match your Network Properties.  Once set, build and upload the code.
