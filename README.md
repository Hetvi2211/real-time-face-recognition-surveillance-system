# Real-Time Face Recognition Surveillance System

## Project Overview

The **Real-Time Face Recognition Surveillance System** is an AI-based security application that detects and recognizes human faces from live video streams using computer vision techniques. The system captures video through a webcam or IP camera, detects faces, converts them into numerical encodings, and compares them with stored face data in a database.

If a match is found, the system displays the person's name and generates alerts. If no match is found, the person is marked as **Unknown** and logged for future analysis.

This project demonstrates practical implementation of **Computer Vision, Machine Learning, and Real-Time System Design**.

---

# Project Goal

To build an **automated real-time surveillance system** capable of identifying individuals using AI-based face recognition to enhance security.

---

# Objectives

* Capture real-time video from a webcam or IP camera
* Detect human faces using computer vision techniques
* Generate facial encodings using AI models
* Match detected faces with stored database
* Display identity of recognized individuals
* Generate alerts for detection events
* Maintain logs of detected individuals

---

# Features

* Upload person image with name
* Store face data in database
* Start/Stop monitoring system
* Real-time video capture
* Face detection and recognition
* Display recognized person's name
* Show **Unknown** for unmatched faces
* Alert notification system
* Detection logs storage

---

# System Architecture

```
Camera Input
      │
      ▼
Face Detection (OpenCV)
      │
      ▼
Face Encoding (face_recognition / dlib)
      │
      ▼
Database Comparison (SQLite)
      │
      ▼
Recognition Result
   ┌───────────────┐
   │ Known Person  │ → Display Name + Alert
   │ Unknown Face  │ → Log Data
   └───────────────┘
```

---

# Tech Stack

## Programming Language

* Python 3.8+

## Libraries

* OpenCV
* face_recognition (dlib)
* NumPy
* Streamlit / Flask

## Tools

* VS Code / PyCharm
* Git & GitHub

## Database

* SQLite

---

# Hardware Requirements

* Laptop / PC (Minimum 8GB RAM)
* Webcam or IP Camera
* Intel i5 Processor or higher

---

# Software Requirements

* Python 3.8+
* OpenCV
* face_recognition
* NumPy
* Streamlit or Flask
* SQLite

---

# Learning Outcomes

* Understanding **Computer Vision concepts**
* Hands-on experience with **Face Recognition**
* Designing **Real-time AI systems**
* **Database integration** with Python
* **Team collaboration using GitHub**

---

# Team Responsibilities

### DHARA

* Frontend Development (Streamlit / Flask UI)
* Database design and integration
* Alert notification system

### HETVI

* Face detection and recognition logic
* OpenCV integration
* Model optimization

---

# Limitations of Existing Systems

* High cost of commercial surveillance systems
* Limited customization
* Dependency on internet or cloud services
* Privacy concerns

---

# Innovation in This Project

* Lightweight real-time face recognition
* Fully **offline working system**
* Custom database for known faces
* Integrated alert system

---

# Future Enhancements

* Mobile application integration
* Cloud database (Firebase / MySQL)
* Multi-camera surveillance support
* Face mask detection
* Emotion detection
* SMS / Email alert system

---
