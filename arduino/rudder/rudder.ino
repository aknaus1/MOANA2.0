
/*
 * CAN port receiver example
 * Receives data on the CAN buss and prints to the serial port
 */

#include <ASTCanLib.h>    
#include <Servo.h>
#include <Wire.h>

#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Servo rudder;

#define MESSAGE_ID        3       // Message ID
#define MESSAGE_PROTOCOL  1       // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH    8       // Data length: 8 bytes
#define MESSAGE_RTR       0       // rtr bit

#define BNO055_SAMPLERATE_DELAY_MS 10
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
#define dirPin 8
#define stepPin 7

float xpos = 0;
float ypos = 0;
float zpos = 0;
int counter = 100;

// Function prototypes
void serialPrintData(st_cmd_t *msg);

// CAN message object
st_cmd_t Msg;

// Buffer for CAN data
uint8_t Buffer[8] = {};

void setup() {
  // Assign PIN 6 to servo, with range between 850ms and 2350ms
  rudder.attach(6, 850, 2350);
 
  canInit(500000);            // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);       // start serial port
  Msg.pt_data = &Buffer[0];    // reference message data to buffer
 
  // Initialise CAN packet.
  // All of these will be overwritten by a received packet
  Msg.ctrl.ide = MESSAGE_PROTOCOL;  // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext   = MESSAGE_ID;        // Set message ID
  Msg.dlc      = MESSAGE_LENGTH;    // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;       // Set rtr bit

  // IMU Code
  Serial.println("Orientation Sensor Test"); Serial.println("");  /* Initialise the sensor */
  if (!bno.begin()) {
    /* There was a problem detecting the BNO055 ... check your connections */
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while (1);
  }
  delay(1000);
  bno.setExtCrystalUse(true);
}

void loop() {
  Serial.println("GETTING SENSOR YDATA:");
  sensors_event_t event;
  bno.getEvent( & event);
  ypos = event.orientation.z;
  xpos = event.orientation.x;
  Serial.println("Outside ypos : ");
  Serial.println(ypos);
  Serial.println("Orientation: ");
  Serial.println(xpos);

/*
  // Clear the message buffer
  clearBuffer(&Buffer[0]);
 
  // Send command to the CAN port controller
  Msg.cmd = CMD_RX_DATA;
 
  // Wait for the command to be accepted by the controller
  while(can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while(can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  // Data is now available in the message object
  // Print received data to the terminal
  serialPrintData(&Msg);

  int temp, id;
  id = Msg.pt_data[0];

*/
  int temp;
  if(xpos < 180)
    temp = xpos /9 * -1;
  else
    temp = xpos /9;
/*
  if(id == 3){
    //     Serial.print("accepted message\n");
//     Serial.print("Moving servo to position: ");
//     Serial.print(Msg.pt_data[1]);
//     Serial.print("\n");
    temp = Msg.pt_data[1];
  }*/
    rudder.write(temp);
}




void serialPrintData(st_cmd_t *msg){
  char textBuffer[50] = {0};
  if (msg->ctrl.ide>0){
    sprintf(textBuffer,"id %d ",msg->id.ext);
  }
  else
  {
    sprintf(textBuffer,"id %04x ",msg->id.std);
  }
  Serial.print(textBuffer);
 
  //  IDE
  sprintf(textBuffer,"ide %d ",msg->ctrl.ide);
  Serial.print(textBuffer);
  //  RTR
  sprintf(textBuffer,"rtr %d ",msg->ctrl.rtr);
  Serial.print(textBuffer);
  //  DLC
  sprintf(textBuffer,"dlc %d ",msg->dlc);
  Serial.print(textBuffer);
  //  Data
  sprintf(textBuffer,"data ");
  Serial.print(textBuffer);
 
  for (int i =0; i<msg->dlc; i++){
    sprintf(textBuffer,"%02X ",msg->pt_data[i]);
    Serial.print(textBuffer);
  }
  Serial.print("\r\n");
}
