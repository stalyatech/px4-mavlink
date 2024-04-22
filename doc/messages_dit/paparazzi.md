**MAVLink Include Files:**

- [common.xml](../messages/common.md)

**Protocol version:** 3

## Messages

### SCRIPT_ITEM (180) {#SCRIPT_ITEM}

Message encoding a mission script item. This message is emitted upon a request for the next script item.

Field Name | Type | Description
--- | --- | ---
target_system | `uint8_t` | System ID
target_component | `uint8_t` | Component ID
seq | `uint16_t` | Sequence
name | `char[50]` | The name of the mission script, NULL terminated.

### SCRIPT_REQUEST (181) {#SCRIPT_REQUEST}

Request script item with the sequence number seq. The response of the system to this message should be a [SCRIPT_ITEM](#SCRIPT_ITEM) message.

Field Name | Type | Description
--- | --- | ---
target_system | `uint8_t` | System ID
target_component | `uint8_t` | Component ID
seq | `uint16_t` | Sequence

### SCRIPT_REQUEST_LIST (182) {#SCRIPT_REQUEST_LIST}

Request the overall list of mission items from the system/component.

Field Name | Type | Description
--- | --- | ---
target_system | `uint8_t` | System ID
target_component | `uint8_t` | Component ID

### SCRIPT_COUNT (183) {#SCRIPT_COUNT}

This message is emitted as response to [SCRIPT_REQUEST_LIST](#SCRIPT_REQUEST_LIST) by the MAV to get the number of mission scripts.

Field Name | Type | Description
--- | --- | ---
target_system | `uint8_t` | System ID
target_component | `uint8_t` | Component ID
count | `uint16_t` | Number of script items in the sequence

### SCRIPT_CURRENT (184) {#SCRIPT_CURRENT}

This message informs about the currently active SCRIPT.

Field Name | Type | Description
--- | --- | ---
seq | `uint16_t` | Active Sequence

