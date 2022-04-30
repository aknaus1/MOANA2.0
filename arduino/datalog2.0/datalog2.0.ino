#include <SPI.h>
#include <SD.h>
#include <ASTCanLib.h>
#include <Wire.h>

#define MESSAGE_ID 6       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit

#define MESSAGE_TYPE 1
#define IDLE 69

int type = IDLE;

// CAN message object
st_cmd_t Msg;
void CANIn();   // recieve message
int start_time = 0;
int i2cAddress = 0x40;
int i2c_read = 0;
int jetsonRequest =0;
// Buffer for CAN data
uint8_t Buffer[8] = {};
File file_in;

enum sensorSend
{
    DEPTH,
    PITCH,
    YAW,
    STEP_POS,
    TEMP,
    SLIDER,
    BOTH,
    THRUSTER_COMMAND
};

enum IDs
{
    JETSON,
    THRUST = 2,
    RUDDER,
    DEPTH_PITCH = 5,
    DATA,
    MISSION,
    DEPTH_TEMP,
    FAILSAFE
};

void setup()
{
    canInit(500000);          // Initialise CAN port. must be before Serial.begin
    Serial.begin(1000000);    // start serial port
    Msg.pt_data = &Buffer[0]; // reference message data to buffer
    Wire.begin();
    // Initialise CAN packet.
    // All of these will be overwritten by a received packet
    Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
    Msg.id.ext = MESSAGE_ID;         // Set message ID
    Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
    Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit

    Wire.begin(i2cAddress);                // join i2c bus with address #0x40
    Wire.onReceive(receiveEvent); // register event
    Wire.onRequest(sendJetson);
    
    Serial.print("Initializing SD card...");
    // see if the card is present and can be initialized:
    if (!SD.begin(10))
    {
        Serial.println("initialization failed!");
        while (1);
    }
    file_in = SD.open(start_time, FILE_READ);
    Serial.print("Time");
    Serial.print(",");
    Serial.print("ID");
    Serial.print(",");
    Serial.print("Data 0");
    Serial.print(",");
    Serial.print("Data 1");
    Serial.print(",");
    Serial.print("Data 2");
    Serial.print(",");
    Serial.print("Data 3");
    Serial.print(",");
    Serial.print("Data 4");
    Serial.print(",");
    Serial.print("Data 5");
    Serial.print(",");
    Serial.print("Data 6");
    Serial.print(",");
    Serial.println("Data 7");
    Serial.println();
    delay(1000);
}

void loop()
{
    CANIn();
}

void CANIn()
{
    clearBuffer(&Buffer[0]);
    Serial.println("CANin");
    Msg.cmd = CMD_RX_DATA; // Send command to the CAN port controller
    // Wait for the command to be accepted by the controller
    while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
    while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);

    int id = 0;
    
    id = Msg.pt_data[0];
    if (id != MESSAGE_ID) return;
    type = Msg.pt_data[MESSAGE_TYPE];
    
    //write Can data to file
    int dataArr[8];
    id = Msg.id.ext;
    for(int i = 0;i<8;i++){
        dataArr[i] = Msg.pt_data[i];
    }
    File file_out = SD.open(start_time, FILE_WRITE);
    if (start_time == 0)
      start_time == millis();
    // if the file is available, write to it:
    if (file_out) {
        file_out.print(millis() - start_time);file_out.print(",");file_out.print(id,DEC);file_out.print(",");
        file_out.print(dataArr[0],DEC);file_out.print(",");file_out.print(dataArr[1],DEC);file_out.print(",");
        file_out.print(dataArr[2],DEC);file_out.print(",");file_out.print(dataArr[3],DEC);file_out.print(",");
        file_out.print(dataArr[4],DEC);file_out.print(",");file_out.print(dataArr[5],DEC);file_out.print(",");
        file_out.print(dataArr[5,DEC]);file_out.print(",");file_out.print(dataArr[6],DEC);file_out.print(",");
        file_out.println(dataArr[7],DEC);
    
        file_out.close();
        Serial.println("Saved");
    }
    // if the file isn't open, pop up an error:
    else {
        Serial.println("error opening data.txt");
    }

}

void sendJetson()
{
    if(jetsonRequest == 0){
        int i = 0;
        while(i < 8)
        {
            Serial.print(Buffer[i]);
            Serial.print(" ");
            Wire.write(Buffer[i++]);
        }
        Serial.println("End send Jetson");
        return;
    }
    else if (jetsonRequest == 1){
        char Buffer[50];
        
        if(file_in.read(Buffer, 50) == -1) 
        {
          Buffer[0] = '\0';
        }

        Wire.write(Buffer, 50);
    }
}

void receiveEvent()
{
    jetsonRequest = Wire.read();
}
