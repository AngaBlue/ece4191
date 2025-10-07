#include <WiFi.h>
#include <WiFiUdp.h>
#include <driver/i2s.h>

// WiFi credentials
const char* ssid = "Kunal";
const char* password = "Varadachari1";

// UDP settings
const char* udpAddress = "172.30.102.252"; // Target IP address
const unsigned int udpDataPort = 12345;   // Data port
WiFiUDP udpData;

#define I2S_WS               12
#define I2S_SD               13
#define I2S_SCK              14
#define I2S_SAMPLE_BIT_COUNT 16
#define SOUND_SAMPLE_RATE    44100
#define SOUND_CHANNEL_COUNT  1
#define I2S_PORT             I2S_NUM_0

const int I2S_DMA_BUF_COUNT = 8;
const int I2S_DMA_BUF_LEN = 1024;
const int StreamBufferNumBytes = 256;
const int StreamBufferLen = StreamBufferNumBytes / 2;
int16_t StreamBuffer[StreamBufferLen];

esp_err_t i2s_install() {
  uint32_t mode = I2S_MODE_MASTER | I2S_MODE_RX;
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(mode/*I2S_MODE_MASTER | I2S_MODE_RX*/),
    .sample_rate = SOUND_SAMPLE_RATE,
    .bits_per_sample = i2s_bits_per_sample_t(I2S_SAMPLE_BIT_COUNT),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = 0,
    .dma_buf_count = I2S_DMA_BUF_COUNT/*8*/,
    .dma_buf_len = I2S_DMA_BUF_LEN/*1024*/,
    .use_apll = false
    };
    return i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

esp_err_t i2s_setpin() {
  const i2s_pin_config_t pin_config = {
    .mck_io_num = I2S_PIN_NO_CHANGE,
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,   
    .data_out_num = I2S_PIN_NO_CHANGE/*-1*/,
    .data_in_num = I2S_SD
  };
  return i2s_set_pin(I2S_PORT, &pin_config);
}
 
// Connections to INMP441 I2S microphone
// #define I2S_WS 12
// #define I2S_SD 13
// #define I2S_SCK 14
 
// // Use I2S Processor 0
// #define I2S_PORT I2S_NUM_0
// #define I2S_WS 12
// #define I2S_SD 13
// #define I2S_SCK 14
// #define I2S_SAMPLE_BIT_COUNT 16
// #define SOUND_SAMPLE_RATE 8000
// #define I2S_PORT I2S_NUM_0
 
// // Define input buffer length
// #define bufferLen 512
// int16_t  sBuffer[bufferLen];
//Sampling rate
// #define SAMPLE_RATE 8000
 
// void i2s_install() {
//   // Set up I2S Processor configuration
//   const i2s_config_t i2s_config = {
//     .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
//     .sample_rate = SAMPLE_RATE,
//     .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
//     .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
//     .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
//     .intr_alloc_flags = 0,
//     .dma_buf_count = 8,
//     .dma_buf_len = bufferLen,
//     .use_apll = false
//   };
 
//   i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
// }

// void i2s_setpin() {
//   // Set I2S pin configuration
//   const i2s_pin_config_t pin_config = {
//     .bck_io_num = I2S_SCK,
//     .ws_io_num = I2S_WS,
//     .data_out_num = -1,
//     .data_in_num = I2S_SD
//   }; 
//   i2s_set_pin(I2S_PORT, &pin_config);
// }

void connectToWiFi() {
  Serial.printf("Connecting to %s", ssid);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.println(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi\n");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nFailed to connect to WiFi\n");
    ESP.restart();
  }
}

// Simple WiFi connection check
void checkWiFiConnection() {
  static unsigned long lastCheck = 0;
  
  if (millis() - lastCheck > 5000) { // Check every 5 seconds
    lastCheck = millis();
    
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected. Attempting to reconnect...\n");
      WiFi.disconnect();
      WiFi.reconnect();
      
      int attempts = 0;
      while (WiFi.status() != WL_CONNECTED && attempts < 10) {
        delay(500);
        Serial.println(".");
        attempts++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nReconnected to WiFi\n");
      } else {
        Serial.println("\nFailed to reconnect to WiFi\n");
      }
    }
  }
}

void setup() {
  Serial.begin(115200);  
  // Connect to WiFi
  connectToWiFi();
  
  // Start UDP
  Serial.printf("Starting UDP data port %d", udpDataPort);
  udpData.begin(udpDataPort);
  Serial.print(WiFi.localIP());
  

  Serial.printf("ESP32-CAM IP: %s\n", WiFi.localIP().toString().c_str());
  delay(1000);
  pinMode(GPIO_NUM_4, OUTPUT);
 
  // Set up I2S
  Serial.println("SETUP MIC ...");

  // set up I2S
  if (i2s_install() != ESP_OK) {
    Serial.println("XXX failed to install I2S");
  }
  if (i2s_setpin() != ESP_OK) {
    Serial.println("XXX failed to set I2S pins");
  }
  if (i2s_zero_dma_buffer(I2S_PORT) != ESP_OK) {
    Serial.println("XXX failed to zero I2S DMA buffer");
  }
  if (i2s_start(I2S_PORT) != ESP_OK) {
    Serial.println("XXX failed to start I2S");
  }

  Serial.println("... DONE SETUP MIC");
  delay(500);
}

void loop() {  
  // digitalWrite(GPIO_NUM_4, HIGH);
  //char sending[] = "Hello World";
  //char inv[] = ~sBuffer;
  // size_t bytesIn = 0;
  // esp_err_t result = i2s_read(I2S_PORT, &sBuffer, sizeof(sBuffer), &bytesIn, portMAX_DELAY);//sizeof(int8_t) * 
  size_t bytesRead = 0;
  esp_err_t result = i2s_read(I2S_PORT, &StreamBuffer, StreamBufferNumBytes, &bytesRead, portMAX_DELAY);
  // for (int i = 0; i < 10; i++)
  // {
  // Serial.println(bytesIn);
  // }
  int samplesRead = 0;
  int16_t *sampleStreamBuffer = StreamBuffer;
  if (result == ESP_OK)
  {
    // digitalWrite(GPIO_NUM_4, HIGH);
    samplesRead = bytesRead / 2;
    udpData.beginPacket(udpAddress, udpDataPort);
    udpData.write((uint8_t*)StreamBuffer, bytesRead);
    //udpData.write((const uint8_t*)sending, sizeof(sending));
    udpData.endPacket(); 
    // digitalWrite(GPIO_NUM_4, LOW);
    //Serial.printf("%d\n",sending);
  }
  // Send left channel data via UDP data port
  
  // Small delay to prevent watchdog timer issues
  delay(1);
}