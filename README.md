# ☁ CloudHero — Cloud Security Learning Platform

A complete, interactive cloud security learning platform built with **Python Flask + SQLite**.
Go from Cloud Zero to Cloud Security Hero with structured topics, rich content, and quizzes that track your real progress.

---

## Features
- 📚 **14 Topics** covering everything from "What is Cloud?" to Career Roadmap
- 📝 **70+ Quiz Questions** across all topics and subtopics
- 📊 **Progress Tracking** via SQLite — persists across sessions
- ✅ **Motivational Feedback** for correct and wrong answers
- 🎯 **Visual Dashboard** with progress ring, per-topic scores, completion tracking
- 🗺 **Learning Roadmap** with visual completion status
- 🎨 **White & Blue Theme** — clean, professional, fully responsive

---

## Setup & Run

### 1. Prerequisites
- Python 3.8+
- pip

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

The SQLite database (`cloudhero.db`) is created automatically on first run.

---

## Project Structure
```
cloud_hero/
├── app.py                  # Flask app, routes, quiz data
├── requirements.txt
├── cloudhero.db            # SQLite database (auto-created)
├── templates/
│   ├── base.html           # Base layout with navbar
│   ├── index.html          # Home page
│   └── topic.html          # Topic + quiz page
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js         # Shared JS (nav progress)
        ├── home.js         # Dashboard & roadmap
        └── topic.js        # Content render & quiz engine
```

---

## Topics Covered
1. What is Cloud Computing?
2. History of Cloud
3. Cloud Service Models (IaaS, PaaS, SaaS)
4. Types of Cloud (Public, Private, Hybrid, Multi-cloud)
5. Major Cloud Providers (AWS, Azure, GCP)
6. Cloud Security Overview
7. Cloud Security Principles (Zero Trust, IAM, Encryption)
8. Cloud Security Threats (DDoS, Breaches, Misconfigurations)
9. Cloud Security Tools (CSPM, SIEM, WAF, Vault)
10. Compliance & Standards (GDPR, SOC2, PCI-DSS, HIPAA)
11. Cloud Networking (VPC, Load Balancing, CDN)
12. Cloud Storage (Object, Block, File)
13. Cloud & DevOps (CI/CD, IaC, Kubernetes)
14. Cloud Career Roadmap

---

## How Progress Tracking Works
- Each quiz answer is stored in `quiz_results` table
- When ≥60% of a topic's questions are correct, the topic is marked **completed**
- Overall progress shown as a percentage in the dashboard and nav bar
- Reset progress anytime from the dashboard

---

## Database Schema
```sql
topics         -- topic metadata
progress       -- per-topic completion, score, attempts
quiz_results   -- individual question answers with timestamps
```

---

## License
Free to use and modify for educational purposes.
