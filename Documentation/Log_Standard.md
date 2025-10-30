# STANDARD LOG FORMAT (JSON Schema)

This schema defines the mandatory structure for all converted logs (DB, OS, Network) used by the system's analysis modules. All raw data must be mapped to this format for integration.

## Example JSON Structure (Mandatory Fields)
```json
{
  "Timestamp_ISO": "2025-10-30T22:30:15.123Z",
  "LogType": "NET",
  "UserID": "projectuser",
  "Action": "TCP_FLOW_START",
  "Source_IP": "192.168.56.20",
  "Feature_Value": 0.057, 
  "Feature_Unit": "seconds (IAT)",
  "Raw_Payload": "Destination: 192.168.56.10:5432"
}
