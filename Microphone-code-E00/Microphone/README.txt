The .cpp file has the code from the .io file just for ease of access but the .io does all the set up with our esp32-cam pins
I have left the files here so they are easy to find it might be best to copy them into the proper directories after, just for all includes from the cpp file
---------------
Changes that need to be made to the cpp file:
1. wifi credentials
2. ipv4 address of the computer you want to send data to

Changes that need to be made to the .py file:
1. line 54, the path for the .wav file is currently specific to my computer that will need to be changed, not sure why it didn't work properly by using relative path but I had an issue with that so its currently hardcoded to my path