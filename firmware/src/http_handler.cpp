// http_handler.cpp
#include "http_handler.h"

HttpHandler::HttpHandler(WebServer& server, MotorControl& motorControl)
    : server_(server), motorControl_(motorControl) {}

void HttpHandler::begin() {
    server_.on("/move", [this]() { this->handleMove(); });
}

void HttpHandler::handleMove() {
    if (!server_.hasArg("translation") || !server_.hasArg("rotation")) {
        server_.send(400, "text/plain", "Missing args");
        return;
    }

    float translation = server_.arg("translation").toFloat();
    float rotation = server_.arg("rotation").toFloat();

    // Compute wheel velocities normalized [-1,1]
    float left = constrain(translation - rotation, -1.0f, 1.0f);
    float right = constrain(translation + rotation, -1.0f, 1.0f);

    motorControl_.setVelocity(left, right);

    server_.send(200, "text/plain", "Move command received");
}
