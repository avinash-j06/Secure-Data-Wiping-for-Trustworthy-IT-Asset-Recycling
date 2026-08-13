# 🛡️ FormatX – Secure Data Wiping Tool

> A Python-based secure data wiping tool designed to support trustworthy IT asset recycling by permanently overwriting data and providing verification and wipe certification.

## 📌 Project Overview

**FormatX** is a secure data wiping application developed to help users permanently erase sensitive data before recycling, donating, or disposing of storage devices.

Unlike normal file deletion or formatting, the tool focuses on **secure overwriting**, helping reduce the possibility of data recovery.

The application includes drive detection, multiple wiping methods, verification, logging, and certificate generation.

---

## ✨ Features

- 🔍 Automatic drive detection
- 🗑️ Secure data wiping
- 🔄 Multiple overwrite methods
- ✅ Data wipe verification
- 📜 Wipe certificate generation
- 📝 Wipe activity logging
- 🖥️ User-friendly Python GUI
- 🔐 Helps support secure IT asset recycling

---

## 🛠️ Technologies Used

- **Python**
- **Tkinter** – Graphical User Interface
- **PSUtil** – Drive and system information
- **ReportLab** – Certificate generation
- **Pillow** – Image processing

---

## 📂 Project Structure

```text
Secure-Data-Wiping-for-Trustworthy-IT-Asset-Recycling/
│
├── main.py
├── wipe_methods.py
├── verification.py
├── drive_detection.py
├── certificate_generator.py
│
├── README.md
├── requirements.txt
└── .gitignore
