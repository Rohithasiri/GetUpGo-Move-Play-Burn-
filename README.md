# GetUpGo
<!-- <div style="display: flex; align-items: center;">
  <img src="https://github.com/your-repo/GetUpGo/preview/icon.png" alt="icon" style="height:100px;width:100px;">
</div> -->

## Table of Contents
- [Introduction](#introduction) <br>
- [Requirements](#requirements) <br>
- [How to use](#installation-and-usage) <br>
- [Preview](#previews) <br>
- [Team](#team-details) <br>
- [Contribution](#contribution) <br>
- [Improvements](#improvements) 

## Abstract
<p align="left">      
GetUpGo is an AI-based fitness and posture correction system that uses real-time pose detection through a webcam to guide users while performing exercises or yoga poses. It provides instant feedback on posture accuracy, counts repetitions, and even allows users to play interactive motion-controlled games like Subway Surfers or the Dinosaur game based on body movements. The system helps users maintain correct form, avoid injury, and stay motivated during workouts.
</p>

## Requirements
|||
|--|--|
| Python | [3.10 or later](https://www.python.org/downloads/) |
| MediaPipe | [0.10.9](https://developers.google.com/mediapipe) |
| OpenCV | [4.9.0](https://pypi.org/project/opencv-python/) |
| NumPy | [1.26.4](https://numpy.org/) |
| PyGame | [2.5.2](https://www.pygame.org/news) |

## Installation and usage

### Step 1: Clone the repository
```bash
git clone https://github.com/your-repo/GetUpGo.git
cd GetUpGo
```

### Step 2: Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # for Linux/Mac
venv\Scripts\activate     # for Windows
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the project
```bash
python main.py
```

### Step 5: How it works
- The system activates your webcam and detects your real-time pose.  
- Choose between **Exercise Mode** and **Game Mode**.  
  - In **Exercise Mode**, perform workouts like **push-ups**, **planks**, **lunges**, or **yoga**.  
    - GetUpGo provides **live posture correction**, **rep counting**, and **calorie estimation**.  
  - In **Game Mode**, you can control games such as **Subway Surfers** or **Chrome Dinosaur** using your body movements.  


## Preview
Screenshots of the project<br>
<img src="https://github.com/AAC-Open-Source-Pool/25AACR06/blob/main/preview%20images/3.png">
<img src="https://github.com/AAC-Open-Source-Pool/25AACR06/blob/main/preview%20images/1.png">
<img src="https://github.com/AAC-Open-Source-Pool/25AACR06/blob/main/preview%20images/2.png">



## Contribution 
**This section provides instructions and details on how to submit a contribution via a pull request. It is important to follow these guidelines to make sure your pull request is accepted.**
1. Before choosing to propose changes to this project, it is advisable to go through the readme.md file of the project to get the philosophy and the motive that went behind this project. The pull request should align with the philosophy and the motive of the original poster of this project.
2. To add your changes, make sure that the programming language in which you are proposing the changes should be the same as the programming language that has been used in the project. The versions of the programming language and the libraries(if any) used should also match with the original code.
3. Write a documentation on the changes that you are proposing. The documentation should include the problems you have noticed in the code(if any), the changes you would like to propose, the reason for these changes, and sample test cases. Remember that the topics in the documentation are strictly not limited to the topics aforementioned, but are just an inclusion.
4. Submit a pull request via [Git etiquettes](https://gist.github.com/mikepea/863f63d6e37281e329f8) 

## Improvements
1. Add calorie tracking visualizations and user progress analytics.
2. Expand to support more exercises like side leg raises, squats, and jumping jacks.
3. Include a leaderboard and daily fitness challenges.
4. Build a mobile companion app for tracking on the go.
5. Deploy as a web application for easy browser-based access.
