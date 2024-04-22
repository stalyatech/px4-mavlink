**MAVLink Include Files:**

- [common.xml](../messages/common.md)

## Messages

### CUBEPILOT_RAW_RC (50001) {#CUBEPILOT_RAW_RC}

Raw RC Data

Field Name | Type | Description
--- | --- | ---
rc_raw | `uint8_t[32]`| 

### HERELINK_VIDEO_STREAM_INFORMATION (50002) {#HERELINK_VIDEO_STREAM_INFORMATION}

Information about video stream

Field Name | Type | Units | Description
--- | --- | --- | ---
camera_id | `uint8_t` |  | Video Stream ID (1 for first, 2 for second, etc.)
status | `uint8_t` |  | Number of streams available.
framerate | `float` | Hz | Frame rate.
resolution_h | `uint16_t` | pix | Horizontal resolution.
resolution_v | `uint16_t` | pix | Vertical resolution.
bitrate | `uint32_t` | bits/s | Bit rate.
rotation | `uint16_t` | deg | Video image rotation clockwise.
uri | `char[230]` |  | Video stream URI (TCP or RTSP URI ground station should connect to) or port number (UDP port ground station should listen to).

### HERELINK_TELEM (50003) {#HERELINK_TELEM}

Herelink Telemetry

Field Name | Type | Description
--- | --- | ---
rssi | `uint8_t`| 
snr | `int16_t`| 
rf_freq | `uint32_t`| 
link_bw | `uint32_t`| 
link_rate | `uint32_t`| 
cpu_temp | `int16_t`| 
board_temp | `int16_t`| 

### CUBEPILOT_FIRMWARE_UPDATE_START (50004) {#CUBEPILOT_FIRMWARE_UPDATE_START}

Start firmware update with encapsulated data.

Field Name | Type | Units | Description
--- | --- | --- | ---
target_system | `uint8_t` |  | System ID.
target_component | `uint8_t` |  | Component ID.
size | `uint32_t` | bytes | FW Size.
crc | `uint32_t` |  | FW CRC.

### CUBEPILOT_FIRMWARE_UPDATE_RESP (50005) {#CUBEPILOT_FIRMWARE_UPDATE_RESP}

offset response to encapsulated data.

Field Name | Type | Units | Description
--- | --- | --- | ---
target_system | `uint8_t` |  | System ID.
target_component | `uint8_t` |  | Component ID.
offset | `uint32_t` | bytes | FW Offset.

