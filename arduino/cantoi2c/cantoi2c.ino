
/*
 * CAN port receiver example
 * Repeatedly transmits an array of test data to the CAN port
 
  * Creates 8 integer array to send as CAN command
 */

#include <ASTCanLib.h>
#include <Wire.h>

#define MESSAGE_ID        0         // Message sender ID
#define MESSAGE_PROTOCOL  1         // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH    8         // Data length: 8 bytes
#define MESSAGE_RTR       0         // rtr bit

int i2cAddress = 0x40;
int i2c_read = 0;
int counter = 0;
int count = 0;

// @ANDREW use this
uint8_t conv_arr[3] = {};

// CAN message object
st_cmd_t Msg;

// Transmit buffer
uint8_t Buffer[8] = {};
uint8_t data[8] = {};
void CANin();


void setup() 
{ 
  canInit(500000);                  // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);             // start serial port
  Msg.pt_data = &Buffer[0];      // reference message data to transmit buffer
  
  Msg.ctrl.ide = MESSAGE_PROTOCOL;  // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext   = MESSAGE_ID;        // Set message ID
  Msg.dlc      = MESSAGE_LENGTH;    // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;  
  // Init I2C line
  Wire.begin(i2cAddress);                // join i2c bus with address #0x40
  Wire.onReceive(receiveEvent); // register event
  Wire.onRequest(sendJetson);
}

void loop() 
{
  CANin();
}

// This is called when we send a command over I2C to the CAN network
// All messages are sent in segments of 8, so it tracks when one message ends with a global counter
void receiveEvent(int bytes) {
  Buffer[counter++] = Wire.read();    // read one character from the I2C
  //Serial.println(Buffer[counter++]);
}

void CANin()
{
  Serial.println("CANin");
  clearBuffer(&Buffer[0]);
  Msg.cmd = CMD_RX_DATA;   // Send command to the CAN port controller
  
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  if(Msg.pt_data[0] !=0) return;

  for(int i =0;i<8;i++)
  {
    Serial.print(Buffer[i]);
    Serial.print(" ");
  }
  Serial.println("");
  for(int i= 0;i<8;i++)
    data[i] = Buffer[i];
  
}

void sendJetson()
{
  //Serial.println("Start send Jetson");
 
  counter = 0;
  int i = 0;
  while(i < 8)
  {
    Serial.print(data[i]);
    Serial.print(" ");
    Wire.write(data[i++]);
  }
  Serial.println("End send Jetson");
}


