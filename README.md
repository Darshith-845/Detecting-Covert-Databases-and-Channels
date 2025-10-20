# 🛡️ Covert Database and Covert Channel Detection System

## 🌟 Project Overview
This project is an academic proof-of-concept system designed to detect two advanced security threats within a computerized environment:
1.  **Covert Databases (Data-at-Rest):** Hidden data or steganography within a legitimate database (e.g., hidden fields, unused space).
2.  **Covert Channels (Data-in-Motion/Process Timing):** Hidden communication pathways that transmit information by manipulating shared system resources (e.g., timing delays, CPU load, network packet timing).

The system architecture follows the design principles outlined in our core documentation, focusing on **baselining**, **anomaly detection**, and **correlation** for confirmation.

---

## 👥 Team & Roles (Initial Phase)

| Role | Student | Primary Focus |
| :--- | :--- | :--- |
| **Project Manager & Integration Lead (S1)** | [Your Name] | Infrastructure setup, standardizing log formats, overall integration. |
| **DB Forensics & Evidence Lead (S2)** | [Student 2 Name] | Database installation, logging, evidence collection/preservation. |
| **Network Forensics Lead (S3)** | [Student 3 Name] | Network monitoring (Tshark), traffic baselining, Timing Channel research. |
| **System & Logging Lead (S4)** | [Student 4 Name] | OS auditing (Auditd/Sysmon), system log collection, Storage Channel research. |

---

## 🛠️ Environment Setup Guide

To begin work, every team member must have access to the project environment.

### 1. Virtual Machines (VMs)
The project runs on two isolated Virtual Machines created by the PM:
* **DB-Server (192.168.56.10):** Hosts the target PostgreSQL/MySQL database.
* **Monitoring-Server (192.168.56.20):** Hosts the monitoring tools (Tshark, OS audit logs) and the detection analysis scripts.

**Access:** Connect to the relevant VM assigned to your tasks.

### 2. Repository Structure
All work must be organized into these three directories:

| Directory | Purpose | Who Uses It |
| :--- | :--- | :--- |
| **`Scripts/`** | All Python/Shell scripts for setup, data extraction, and detection logic. | All Members |
| **`Logs/`** | Cleaned, standardized, and anonymized baseline and test log files. | All Members |
| **`Documentation/`** | Research summaries, project reports, and the **Log_Standard.md** file. | All Members |

---

## 📅 Initial Milestones (Days 1-5 Focus)
The immediate priority is completing the **Foundational Setup** and establishing the **Normal Behavior Baseline**.

1.  **System Setup:** All tools (DB, Tshark, Auditing) must be installed and verified.
2.  **Log Standard:** All data must be converted to the format defined in `Documentation/Log_Standard.md`.
3.  **Baseline Collection:** Collect 3-5 days of "normal", non-covert data from the DB, Network, and OS.

**Remember to commit your work daily!**
