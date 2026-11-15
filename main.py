import re
from flask import Flask, request, render_template, jsonify, send_file
import subprocess
import socket
import tempfile
import os

main = Flask(__name__)

def is_valid_target(target):
    if not target:
        return False
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    hostname_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(ip_pattern, target) or re.match(hostname_pattern, target))

def run_gobuster(url):
    wordlist = "/usr/share/wordlists/dirb/common.txt"
    if not os.path.exists(wordlist):
        return "Wordlist tapılmadı (/usr/share/wordlists/dirb/common.txt)."
    command = [
        "gobuster", "dir",
        "-u", url,
        "-w", wordlist,
        "-q", "--no-error",
        "-t", "5",
        "-k",
        "--timeout", "30s"
    ]
    try:
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=90
        )
        return output.strip() if output.strip() else "Gizli qovluq və ya fayl tapılmadı."
    except subprocess.TimeoutExpired:
        return "Gobuster skanı vaxt limitini (90 saniyə) keçdiyi üçün dayandırıldı."
    except subprocess.CalledProcessError as e:
        out = e.output.strip() if e.output else ""
        return out if out else "Veb server cavab vermədi."
    except Exception as e:
        return f"Xəta: {str(e)}"

def run_whatweb(target):
    try:
        url = target if target.startswith("http") else f"http://{target}"
        output = subprocess.check_output(
            ["whatweb", "--color=never", "-a", "1", "--open-timeout", "15", "--read-timeout", "15", url],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60
        )
        return output.strip() if output.strip() else "Texnologiya məlumatı tapılmadı."
    except subprocess.TimeoutExpired:
        return "WhatWeb skanı vaxt limitini keçdi."
    except Exception as e:
        return f"WhatWeb xətası: {str(e)}"

def run_nikto(target):
    try:
        url = target if target.startswith("http") else f"http://{target}"
        output = subprocess.check_output(
            ["nikto", "-h", url, "-Tuning", "123b", "-maxtime", "60s", "-nointeractive"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=75
        )
        lines = [line.strip() for line in output.splitlines() if line.strip().startswith("+")]
        return "\n".join(lines) if lines else (output.strip() or "Kritik veb zəifliyi tapılmadı.")
    except subprocess.TimeoutExpired:
        return "Nikto skanı vaxt limitini (60 saniyə) keçdiyi üçün dayandırıldı."
    except subprocess.CalledProcessError as e:
        out = e.output if e.output else ""
        lines = [line.strip() for line in out.splitlines() if line.strip().startswith("+")]
        return "\n".join(lines) if lines else (out.strip() or "Nikto xətası baş verdi.")
    except Exception as e:
        return f"Nikto xətası: {str(e)}"

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()
    scan_mode = request.form.get("scan_mode", "nmap")
    if not is_valid_target(target):
        return jsonify({"error": "Invalid target"}), 400
    
    ip_target = "Tapılmadı"
    result = ""
    extra_title = ""
    extra_result = ""
    
    try:
        ip_target = socket.gethostbyname(target)
        
        if scan_mode == "nmap":
            result = subprocess.check_output(
                ["nmap", "-sS", "-sV", "-O", "-A", "-T3", target],
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in result.splitlines():
                if 'Nmap scan report for' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        ip_target = parts[-1].strip("()")
                        break

        elif scan_mode == "gobuster":
            extra_title = "Gobuster Directory Scan:"
            gb_logs = []
            for proto in ["http", "https"]:
                url = f"{proto}://{target}"
                gb_out = run_gobuster(url)
                if "cavab vermədi" not in gb_out and "refused" not in gb_out.lower():
                    gb_logs.append(f"[{url}]\n{gb_out}")
            extra_result = "\n\n".join(gb_logs) if gb_logs else f"[http://{target}]\nVeb serverə qoşulmaq mümkün olmadı və ya qovluq tapılmadı."

        elif scan_mode == "whatweb":
            extra_title = "WhatWeb Technology Analysis:"
            extra_result = run_whatweb(target)

        elif scan_mode == "nikto":
            extra_title = "Nikto Web Vulnerability Scan:"
            extra_result = run_nikto(target)

        full_report = result if scan_mode == "nmap" else f"=== {extra_title} ({target}) ===\n{extra_result}"
        scan_file = os.path.join(tempfile.gettempdir(), f"scan_result_{target}.txt")
        with open(scan_file, "w", encoding="utf-8") as f:
            f.write(full_report)

    except subprocess.CalledProcessError as e:
        result = e.output if isinstance(e.output, str) else (e.output.decode() if e.output else "Error running scan.")
    except Exception as e:
        result = f"Skan zamanı xəta baş verdi: {str(e)}"

    return render_template("result_real.html", target=target, ip_target=ip_target, result=result, extra_title=extra_title, extra_result=extra_result)

@main.route('/download/<target>')
def download_report(target):
    scan_file = os.path.join(tempfile.gettempdir(), f"scan_result_{target}.txt")
    if os.path.exists(scan_file):
        return send_file(scan_file, as_attachment=True)
    else:
        return "Scan result file not found.", 404

if __name__ == "__main__":
    main.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
