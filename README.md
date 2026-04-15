# 🚦 Smart Traffic Management System (AI-Based ITMS)

## 📌 Overview
This project is an AI-powered Intelligent Traffic Management System (ITMS) that dynamically controls traffic signals using real-time vehicle detection.

It uses YOLOv8 for object detection and adjusts traffic signals based on:
- Traffic density  
- Ambulance priority  
- Accident handling  

---

## 🎯 Features
- Real-time vehicle detection using YOLOv8  
- Adaptive traffic signal control  
- Emergency vehicle (ambulance) priority override  
- Accident detection simulation & traffic halt  
- Multi-road video simulation  
- Smart decision-making algorithm  

---

## 🧠 How It Works
1. Video input is taken from multiple roads  
2. YOLOv8 detects vehicles in each frame  
3. Vehicle count is calculated for each road  
4. Signal timing is adjusted dynamically  
5. Special conditions:
   - Ambulance → Immediate green signal  
   - Accident → Traffic halted  

---

## 🛠️ Tech Stack
- Python  
- OpenCV  
- YOLOv8 (Ultralytics)  
- NumPy  

---

## 📂 Project Structure