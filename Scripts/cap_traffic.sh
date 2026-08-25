#!/bin/bash

# This script captures network traffic for a specified duration and saves it
# as a CSV file with fields suitable for machine learning analysis.
#
# --- Configuration ---

# DURATION:
# The duration is set in seconds.
# 2 hours = 7200 seconds
# 3 hours = 10800 seconds
# Set to 120 seconds (2 minutes) for easier testing.
# Change this value to 7200 or 10800 for your long capture.
DURATION=14400

# FINAL DESTINATION DIRECTORY (WSL Path to Windows)
# PLEASE UPDATE THIS PATH.
# The path /mnt/c/Users/Go*/Down* is not recommended for a script
# as the wildcards (*) can cause errors during expansion.
# Please provide the full, specific path to your Windows Downloads folder.
# Example: /mnt/c/Users/YourName/Downloads
FINAL_DEST_DIR="/mnt/c/Users/GouriAmit/Downloads"

# --- Helper Function ---

# Naming function to create a unique CSV filename with a timestamp.
# Usage example:
#   local_filename=$(generate_filename)
#   echo "Saving to $local_filename"
#   # Output: Saving to network_capture_2025-11-02_16-20-00.csv
generate_filename() {
  date +"network_capture_%Y-%m-%d_%H-%M-%S.csv"
}

# --- Script Execution ---

# Generate the unique filename
FILENAME=$(generate_filename)

# Set the temporary location to save the file
# /tmp/ is a good place for this, as it's cleared on reboot.
TMP_OUTPUT_FILE="/tmp/$FILENAME"

echo "Starting network capture on 'eth0' for $DURATION seconds..."
echo "Temporary file will be: $TMP_OUTPUT_FILE"
echo "Final destination will be: $FINAL_DEST_DIR/$FILENAME"
echo "You will be prompted for your password as 'tshark' needs admin (sudo) rights."

# --- TSHARK COMMAND ---
#
# -i eth0: Listen on the 'eth0' interface (common for WSL/Linux).
# -a duration:$DURATION: Stop capturing after $DURATION seconds.
# -T fields: Output data in a field-based format (not the raw pcap).
# -E header=y: Include a header row (the field names) at the top of the CSV.
# -E separator=,: Use a comma as the field separator.
# -e ...: Specify the fields (features) we want to extract.
#
# We are capturing:
# - frame.number: The sequential packet number from the capture.
# - frame.time_epoch: The exact timestamp (seconds since 1970-01-01).
# - ip.src: Source IP address.
# - ip.dst: Destination IP address.
# - _ws.col.Protocol: The protocol name (e.g., TCP, UDP, DNS, ICMP).
# - frame.len: The total length of the packet (in bytes).
# - tcp.srcport: TCP source port (will be blank for non-TCP packets).
# - tcp.dstport: TCP destination port.
# - udp.srcport: UDP source port.
# - udp.dstport: UDP destination port.
#
sudo tshark -i eth0 -a duration:$DURATION \
  -T fields \
  -E header=y -E separator=, \
  -e frame.number \
  -e frame.time_epoch \
  -e ip.src \
  -e ip.dst \
  -e _ws.col.Protocol \
  -e frame.len \
  -e tcp.srcport \
  -e tcp.dstport \
  -e udp.srcport \
  -e udp.dstport \
  > "$TMP_OUTPUT_FILE"

echo "---"
echo "Capture complete. Data saved to $TMP_OUTPUT_FILE"

# Check if the destination directory exists
if [ ! -d "$FINAL_DEST_DIR" ]; then
  echo "Error: Destination directory $FINAL_DEST_DIR does not exist."
  echo "Please create it or correct the FINAL_DEST_DIR variable in the script."
  echo "Your file is still available at $TMP_OUTPUT_FILE"
  exit 1
fi

echo "Moving file to $FINAL_DEST_DIR..."
# We use sudo again because the file created by "sudo tshark" is owned by root.
sudo mv "$TMP_OUTPUT_FILE" "$FINAL_DEST_DIR/"

if [ $? -eq 0 ]; then
  echo "Success! File moved to $FINAL_DEST_DIR/$FILENAME"
else
  echo "Error moving file. It is still available at $TMP_OUTPUT_FILE"
fi

echo "You can now run the Python analysis script (point it to the new file location)."


