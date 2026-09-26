# 🚀 Stock-Sense-Hackathon

Welcome to our **Odoo Hackathon Project**! This repository contains an AI-powered, IoT-integrated inventory management system for Odoo 17.

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
Ensure you have:
- **Odoo 17 Community Edition** installed
- **Python 3.8+**
- **Node.js** and **npm** (for the dashboard)
- **Git**

---

### 2. Project Setup

#### 2.1 Clone the Repository
```bash
git clone https://github.com/liakhath/Stock-Sense-Hackathon
cd Stock-Sense-Hackathon
```

#### 2.2 Install Odoo Addons
Copy the addons to your Odoo custom addons path:
```bash
cp -r addons/* /path/to/odoo/addons/
```
Or configure your `addons_path` in your `odoo.conf`:
```ini
addons_path = /path/to/odoo/addons,c:/Users/ASUS/OneDrive/Desktop/odoo/Stock-Sense-Hackathon/addons
```

#### 2.3 Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

### 3. Run Odoo
Start the Odoo server with the `stock_sense_hackathon` module:
```bash
python odoo-bin -u stock_sense_hackathon
```

---

### 4. Install Dashboard (Frontend)
Open a new terminal and navigate to the dashboard directory:
```bash
cd addons/dashboard
npm install
npm run dev
```

---

### 5. Access the Application
- **Odoo Backend**: [http://localhost:8069](http://localhost:8069)
- **React Dashboard**: [http://localhost:3000](http://localhost:3000)

---

## ✨ Features

### 📡 IoT Integration
- Real-time weight/inventory monitoring using **Raspberry Pi**
- Automated stock replenishment based on IoT triggers
- Mobile-friendly stock check interface

### 🧠 AI Forecasting
- **Machine Learning** algorithms (Linear Regression, Random Forest, ARIMA) for demand prediction
- Smart reordering suggestions & automated Purchase Order creation
- Trend analysis and confidence score calculations

### 📊 Enhanced Dashboard
- Modern UI with **ReactJS** and **Tailwind CSS**
- Real-time stock charts and analytics
- Role-based access control (User & Manager)

---

## 🛠️ Tech Stack
- **Odoo Framework**: Odoo 17
- **Frontend**: ReactJS, Tailwind CSS, Chart.js
- **IoT**: Raspberry Pi, Weight & RFID Sensors
- **AI/ML**: Scikit-Learn, Pandas, NumPy, Statsmodels
- **Database**: PostgreSQL
- **Version Control**: Git, GitHub

---

## 📁 Project Structure

```
Stock-Sense-Hackathon/
├── addons/
│   ├── stock_sense_hackathon/    # Main Odoo 17 module
│   │   ├── models/              # Product, Forecast, Alert, & IoT models
│   │   ├── views/               # XML views, forms, kanban, & menus
│   │   ├── security/            # User groups & ir.model.access.csv
│   │   ├── data/                # Automated cron jobs for alert & IoT checks
│   │   └── static/              # CSS/JS web assets
│   ├── stock_sense_iot/         # Raspberry Pi integration features
│   └── dashboard/               # ReactJS frontend
└── requirements.txt             # Python ML & IoT dependencies
```

---

## 🤝 Contributing
1. Create a feature branch: `git checkout -b feature/awesome-feature`
2. Make your changes
3. Submit a pull request


This project is licensed under the MIT License.

**Happy Hacking!** 🚀