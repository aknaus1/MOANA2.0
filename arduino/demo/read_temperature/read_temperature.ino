// REQUIRES the following Arduino libraries:
// - DHT Sensor Library: https://github.com/adafruit/DHT-sensor-library
// - Adafruit Unified Sensor Lib: https://github.com/adafruit/Adafruit_Sensor

#include "DHT.h"
#include <ASTCanLib.h>

#include <Adafruit_Sensor.h>


#include <Wire.h>


#define DHTPIN 5     // Digital pin connected to the DHT sensor
// Feather HUZZAH ESP8266 note: use pins 3, 4, 5, 12, 13 or 14 --
// Pin 15 can work but DHT must be disconnected during program upload.


#define DHTTYPE DHT11   // DHT 22  (AM2302), AM2321

#define MESSAGE_ID 7 // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8 // Data length: 8 bytes
#define MESSAGE_RTR 0 // rtr bit



// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is
// Connect pin 3 (on the right) of the sensor to GROUND (if your sensor has 3 pins)
// Connect pin 4 (on the right) of the sensor to GROUND and leave the pin 3 EMPTY (if your sensor has 4 pins)
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor

// Initialize DHT sensor.
// Note that older versions of this library took an optional third parameter to
// tweak the timings for faster processors.  This parameter is no longer needed
// as the current DHT reading algorithm adjusts itself to work on faster procs.
DHT dht(DHTPIN, DHTTYPE);
float temperature = 0;
// Transmit buffer
uint8_t txBuffer[8] = {};
// CAN message object
st_cmd_t txMsg;
int yposArray[3];

void setup() {
  canInit(500000);                  // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);
  pinMode(4, OUTPUT);
  pinMode(5,INPUT);

  txMsg.pt_data = &txBuffer[0];
  digitalWrite(4,HIGH);
  dht.begin();
}

void convert() {
  float con = temperature;
  int whole, fraction;
  if (con < 0.0) {
    yposArray[0] = 1; // 1 is a negative value
    con = con * -1;
  } else if (con > 0.0) {
    yposArray[0] = 2; // 2 is positive
  } else if (con == 0) {
    yposArray[0] = 0;
  }
  whole = round(con);
  yposArray[1] = whole;
  fraction = con * 100;
  fraction = fraction - (whole * 100);
  yposArray[2] = fraction;



  /*
  Serial.println(testVal);
  Serial.println(yposArray[0]);
  Serial.println(yposArray[1]);
  Serial.println(yposArray[2]);
  */
}

void loop() {
  // Wait a few seconds between measurements.
  delay(1000);
  temperature = dht.readTemperature();
    // Check if any reads failed and exit early (to try again).
  if (isnan(temperature)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  } 
  convert();
  Serial.print(F("%  Temperature: "));
  Serial.print(temperature);

  CANsend();
  //float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  
  // Read temperature as Fahrenheit (isFahrenheit = true)
  //float f = dht.readTemperature(true);


  

  // Compute heat index in Fahrenheit (the default)
  //float hif = dht.computeHeatIndex(f, h);
  // Compute heat index in Celsius (isFahreheit = false)
  //float hic = dht.computeHeatIndex(t, h, false);

}

void CANsend() {
  Serial.println("Temperature:");
  Serial.println(temperature);
  
  convert();
  clearBuffer(&txBuffer[0]);

  txMsg.id.ext = MESSAGE_ID;         // Set message ID
  txBuffer[0] = 6;

  for (int i = 0; i < 7; i++) {
    if (i < 4) {
      txBuffer[i + 1] = yposArray[i];
    } else {
      txBuffer[i + 1];
    }
  } 

  // Setup CAN packet.
  txMsg.ctrl.ide = MESSAGE_PROTOCOL;  // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  txMsg.id.ext   = MESSAGE_ID;        // Set message ID
  txMsg.dlc      = MESSAGE_LENGTH;    // Data length: 8 bytes
  txMsg.ctrl.rtr = MESSAGE_RTR;       // Set rtr bit

  // Send command to the CAN port controller
  txMsg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&txMsg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&txMsg) == CAN_STATUS_NOT_COMPLETED);
}
