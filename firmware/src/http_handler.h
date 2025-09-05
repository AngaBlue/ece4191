// http_handler.h
#pragma once
#include <WebServer.h>
#include "motor_control.h"

class HttpHandler {
public:
    HttpHandler(WebServer& server, MotorControl& motorControl);

    void begin();
    void handleMove();

private:
    WebServer& server_;
    MotorControl& motorControl_;
};
