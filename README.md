# Web Scanner

**Web Scanner** is a modern, neon-themed web reconnaissance and vulnerability scanning dashboard built with Python (Flask) and Gunicorn. It integrates four essential security tools into a single interface.

## Integrated Modules
- **Nmap Scan:** Discovers open ports, service versions, operating system details, and traceroute.
- **Gobuster Scan:** Enumerates hidden directories, admin panels, and sensitive files on web servers.
- **WhatWeb Scan:** Identifies CMS, web servers, frameworks, and backend technologies.
- **Nikto Scan:** Checks web servers for known vulnerabilities, outdated software, and misconfigurations.
- **Report Export:** Download full scan results as `.txt` reports.

## Installation & Usage (Kali Linux)
```bash
git clone https://github.com
cd Web-Scanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo venv/bin/gunicorn -w 1 --timeout 600 -b 0.0.0.0:5000 main:main
```

> **Disclaimer:** This tool is developed strictly for educational purposes and authorized security testing in controlled lab environments.
