# AI Beer Robot

> Building an autonomous robot that can find a beer, navigate to it, and bring it to me.

This project documents my journey from **Software Engineer → AI Robotics Engineer** by building a real autonomous robot from scratch.

I am sharing every step publicly:
- computer vision
- edge AI deployment
- ROS2 architecture
- embedded systems
- motor control
- navigation

---

## 🎥 Follow the journey

I am building this robot day by day and documenting every success, mistake, and engineering problem.

📸 Instagram: https://www.instagram.com/samrondzel/  
▶️ YouTube: https://www.youtube.com/@samrondzel5577

---

# 🚀 Goal

The final robot should:

✅ Detect a beer bottle using AI  
✅ Track the target in real time  
✅ Navigate autonomously  
✅ Avoid obstacles  
✅ Control motors using embedded hardware  
⬜ Pick up and deliver the beer  

---

# 🧠 System Architecture


Camera
│
▼
Raspberry Pi
│
├── YOLO Object Detection
│
├── Kalman Tracking
│
├── ROS2 Decision System
│
▼
ESP32
│
├── PWM Motor Control
│
├── Encoder Feedback
│
▼
Motor Driver
│
▼
Wheels


---

# 🛠️ Tech Stack

## Computer Vision

- YOLO object detection
- OpenCV
- Model optimization for edge devices

What I learned:

- Running AI models on limited hardware
- Optimizing inference speed
- Deploying neural networks outside a laptop


---

## 🤖 Robotics

- ROS2
- Publisher / Subscriber architecture
- Multiple independent nodes

Current nodes:

```

camera_node
│
▼
detector_node
│
▼
tracker_node
│
▼
control_node

```

---

## 🧮 State Estimation

Implemented:

- Kalman Filter
- Object tracking
- Prediction when detection is lost


---

## ⚡ Embedded Systems

Hardware:

- Raspberry Pi
- ESP32
- TB6612FNG Motor Driver
- DC motors with encoders

ESP32 handles:

- PWM signals
- motor timing
- low level control


---

# 📅 Build Progress

## Day 1 — Computer Vision

Started with YOLO object detection.

Goal:
Give the robot eyes.

Status:
✅ Working


---

## Day 5 — Raspberry Pi Deployment

Problem:

Running AI on small hardware is harder than expected.

Tried:

❌ PyTorch  
❌ OpenVINO  

Solution:

✅ NCNN optimized inference


---

## Day 10 — ROS2

Moved from one huge Python script:

```

camera → detection → control

```

to modular robotics architecture:

```

camera node
↓
AI node
↓
tracking node
↓
motor node

```

---

## Day 15 — Hardware Control

Learning:

- GPIO
- PWM
- ESP32
- motor drivers

Status:
🚧 In progress


---

# 📂 Repository Structure

```

src/
├── beer_robot_ros2/
│
├── ESP32/
│
└── models/

docs/
├── architecture.md
├── hardware.md
└── mistakes.md

```

---

# 🧩 Why I am building this

Modern robotics combines:

- Artificial Intelligence
- Computer Vision
- Control Theory
- Embedded Systems
- Mechanical Engineering

Instead of only learning theory, I decided to build a complete robot and document the entire process.

---

# 🔮 Future Projects

This is Season 1.

Next:

🤖 Robot Arm  
🚁 AI Drone  
🦾 Humanoid Robotics Experiments


---

# ⭐ Follow

If you are interested in robotics, AI, or building intelligent machines:

Follow the journey and build with me.
