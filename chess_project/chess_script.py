import streamlit as st
import json
import time
import re
import requests
import google.generativeai as genai
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import chess
import chess.pgn
import math
import tqdm
import os
from stockfish import Stockfish
import io


GEMINI_API_KEY = "secret"

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to configure Gemini API: {e}")

STOCKFISH_EXECUTABLE_PATH = "/opt/homebrew/bin/stockfish"


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    html, body, [class*="stApp"] {
        background: linear-gradient(135deg, #2A3132 0%, #336B87 25%, #2A3132 50%, #336B87 75%, #2A3132 100%);
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
        color: #ffffff;
        overflow-x: hidden;
    }
    
    .main {
        background: transparent;
        padding: 0;
    }
    
    .stApp {
        background: transparent;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(144, 175, 197, 0.12) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(51, 107, 135, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(118, 54, 38, 0.08) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
        animation: backgroundFloat 30s ease-in-out infinite;
    }
    
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20% 30%, rgba(144, 175, 197, 0.25), transparent),
            radial-gradient(2px 2px at 60% 70%, rgba(51, 107, 135, 0.25), transparent),
            radial-gradient(1px 1px at 50% 50%, rgba(118, 54, 38, 0.2), transparent),
            radial-gradient(1px 1px at 80% 10%, rgba(144, 175, 197, 0.2), transparent),
            radial-gradient(2px 2px at 90% 80%, rgba(51, 107, 135, 0.15), transparent);
        background-size: 200% 200%;
        background-position: 0% 0%, 100% 0%, 50% 100%, 0% 100%, 100% 100%;
        pointer-events: none;
        z-index: 0;
        animation: particlesFloat 40s linear infinite;
        opacity: 0.5;
    }
    
    @keyframes backgroundFloat {
        0%, 100% { transform: translate(0, 0) scale(1); opacity: 1; }
        33% { transform: translate(30px, -30px) scale(1.1); opacity: 0.9; }
        66% { transform: translate(-20px, 20px) scale(0.95); opacity: 0.85; }
    }
    
    @keyframes particlesFloat {
        0% { background-position: 0% 0%, 100% 0%, 50% 100%, 0% 100%, 100% 100%; }
        25% { background-position: 100% 100%, 0% 100%, 100% 0%, 50% 0%, 0% 0%; }
        50% { background-position: 50% 50%, 50% 50%, 0% 0%, 100% 100%, 50% 50%; }
        75% { background-position: 0% 100%, 100% 0%, 50% 50%, 0% 0%, 100% 100%; }
        100% { background-position: 0% 0%, 100% 0%, 50% 100%, 0% 100%, 100% 100%; }
    }
    
    h1 {
        font-weight: 300;
        letter-spacing: -0.05em;
        color: #ffffff;
        font-size: 4.5rem;
        margin: 0;
        line-height: 1.1;
        background: linear-gradient(135deg, #90AFC5 0%, #336B87 50%, #90AFC5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        background-size: 200% 200%;
        animation: fadeInDown 1.2s cubic-bezier(0.16, 1, 0.3, 1), gradientText 8s ease infinite;
        position: relative;
        filter: drop-shadow(0 0 20px rgba(144, 175, 197, 0.2));
    }
    
    h1::after {
        content: '';
        position: absolute;
        bottom: -12px;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #90AFC5, #336B87, #763626, transparent);
        animation: expandLine 1.4s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both, gradientShift 3s ease infinite;
        box-shadow: 0 0 15px rgba(144, 175, 197, 0.3);
    }
    
    @keyframes gradientText {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    h2 {
        font-weight: 400;
        letter-spacing: -0.03em;
        color: #ffffff;
        font-size: 2.5rem;
        margin-top: 4rem;
        margin-bottom: 1.5rem;
        line-height: 1.3;
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        opacity: 0;
        animation-fill-mode: forwards;
        background: linear-gradient(135deg, #90AFC5 0%, #336B87 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 15px rgba(144, 175, 197, 0.15));
    }
    
    h3 {
        font-weight: 500;
        letter-spacing: -0.02em;
        color: #ffffff;
        font-size: 1.75rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        background: linear-gradient(135deg, #90AFC5 0%, #336B87 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    p {
        color: rgba(255, 255, 255, 0.6);
        line-height: 1.8;
        font-weight: 300;
        font-size: 1rem;
        letter-spacing: 0.01em;
    }
    
    fieldset,
    fieldset * {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-width: 0 !important;
    }
    
    .stTextInput, .stNumberInput {
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stTextInput *,
    .stTextInput *::before,
    .stTextInput *::after,
    .stNumberInput *,
    .stNumberInput *::before,
    .stNumberInput *::after {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-width: 0 !important;
        border-style: none !important;
        border-color: transparent !important;
    }
    
    .stTextInput,
    .stNumberInput {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div,
    .stNumberInput > div {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-width: 0 !important;
    }
    
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background: rgba(144, 175, 197, 0.1) !important;
        border: none !important;
        border-width: 0 !important;
        border-style: none !important;
        border-color: transparent !important;
        border-radius: 20px !important;
        backdrop-filter: blur(20px);
        box-shadow: none !important;
        outline: none !important;
        outline-width: 0 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: transparent !important;
        border: none !important;
        border-width: 0 !important;
        border-style: none !important;
        border-color: transparent !important;
        border-radius: 20px !important;
        color: #ffffff !important;
        padding: 1.2rem 1.75rem !important;
        font-size: 1.05rem !important;
        font-weight: 400 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        width: 100% !important;
        outline: none !important;
        outline-width: 0 !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(144, 175, 197, 0.4);
        font-weight: 300;
        letter-spacing: 0.02em;
    }
    
    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        background: rgba(144, 175, 197, 0.15) !important;
        transform: translateY(-2px);
        border: none !important;
        border-width: 0 !important;
        outline: none !important;
        outline-width: 0 !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        outline: none !important;
        outline-width: 0 !important;
        border: none !important;
        border-width: 0 !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div:focus-within *,
    .stNumberInput > div > div:focus-within * {
        border: none !important;
        border-width: 0 !important;
        outline: none !important;
        outline-width: 0 !important;
        box-shadow: none !important;
    }
    
    .stNumberInput button {
        background: rgba(144, 175, 197, 0.15) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #90AFC5 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        width: 32px !important;
        height: 32px !important;
        margin: 4px !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stNumberInput button:hover {
        background: rgba(144, 175, 197, 0.25) !important;
        transform: scale(1.1);
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stNumberInput button:active {
        transform: scale(0.95);
        border: none !important;
        outline: none !important;
    }
    
    .stNumberInput button:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stNumberInput > div > div > div {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stTextInput label,
    .stNumberInput label {
        color: rgba(255, 255, 255, 0.8) !important;
        font-weight: 400 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: 0.02em !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #336B87 0%, #90AFC5 50%, #336B87 100%);
        background-size: 200% 200%;
        color: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 1.25rem 2.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        backdrop-filter: blur(20px);
        width: 100%;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 1.2s cubic-bezier(0.16, 1, 0.3, 1), buttonGradient 4s ease infinite;
        box-shadow: 0 8px 32px rgba(51, 107, 135, 0.3),
                    0 0 0 0 rgba(51, 107, 135, 0.4);
    }
    
    @keyframes buttonGradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 20px 60px rgba(51, 107, 135, 0.5),
                    0 0 0 4px rgba(144, 175, 197, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.25);
        animation: fadeInUp 1.2s cubic-bezier(0.16, 1, 0.3, 1), buttonGradient 2s ease infinite, buttonPulse 1.5s ease infinite;
    }
    
    @keyframes buttonPulse {
        0%, 100% { box-shadow: 0 20px 60px rgba(51, 107, 135, 0.5), 0 0 0 4px rgba(144, 175, 197, 0.25); }
        50% { box-shadow: 0 20px 60px rgba(51, 107, 135, 0.7), 0 0 0 8px rgba(144, 175, 197, 0.15); }
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(1.01);
        transition: transform 0.15s;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(144, 175, 197, 0.12) 0%, rgba(51, 107, 135, 0.15) 100%);
        border: 2px solid rgba(144, 175, 197, 0.25);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        backdrop-filter: blur(30px);
        position: relative;
        overflow: hidden;
        animation: fadeInScale 1s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 12px 40px rgba(42, 49, 50, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(144, 175, 197, 0.18) 0%, rgba(51, 107, 135, 0.2) 100%);
        opacity: 0;
        transition: opacity 0.6s;
    }
    
    .metric-card::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(144, 175, 197, 0.08) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.6s;
        animation: rotateGlow 8s linear infinite;
    }
    
    @keyframes rotateGlow {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .metric-card:hover {
        background: linear-gradient(135deg, rgba(144, 175, 197, 0.2) 0%, rgba(51, 107, 135, 0.25) 100%);
        border-color: rgba(144, 175, 197, 0.5);
        transform: translateY(-8px) scale(1.05);
        box-shadow: 0 32px 100px rgba(42, 49, 50, 0.6),
                    0 0 0 2px rgba(144, 175, 197, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }
    
    .metric-card:hover::before,
    .metric-card:hover::after {
        opacity: 1;
    }
    
    .stMetric {
        background: transparent;
        padding: 0;
    }
    
    .stMetric > div {
        color: #ffffff;
        font-weight: 300;
    }
    
    .stMetric > div > div {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.85rem;
        font-weight: 400;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }
    
    .stMetric > div > div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 200;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    
    .stExpander,
    div[data-testid="stExpander"] {
        background: rgba(0, 0, 0, 0.15) !important;
        border: none !important;
        border-radius: 16px !important;
        margin-bottom: 1rem;
        backdrop-filter: blur(12px);
        box-shadow: none !important;
        transition: transform 0.2s ease;
    }
    
    .stExpander:hover,
    div[data-testid="stExpander"]:hover {
        transform: translateY(-2px);
    }
    
    .stExpander div[role="button"],
    div[data-testid="stExpander"] div[role="button"] {
        border: none !important;
        box-shadow: none !important;
    }
    
    .stContainer {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 2rem 0;
        animation: fadeInScale 1s cubic-bezier(0.16, 1, 0.3, 1);
        backdrop-filter: blur(40px);
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    
    .stContainer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 2px;
        height: 100%;
        background: linear-gradient(180deg, transparent, rgba(255, 255, 255, 0.25), transparent);
        animation: shimmer 4s infinite;
    }
    
    .stContainer::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0.7) 50%, rgba(255, 255, 255, 0.4) 100%);
        background-size: 200% 100%;
        border-radius: 10px;
        animation: progressBar 1s ease-out, shimmerProgress 2s infinite;
        height: 4px;
    }
    
    .stProgress > div > div {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .stTabs > div > div > div > div {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 1rem 2rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stTabs > div > div > div > div[aria-selected="true"] {
        background: transparent;
        color: #ffffff;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        position: relative;
    }
    
    .stTabs > div > div > div > div[aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
        animation: expandLine 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stTabs > div > div > div > div[aria-selected="false"] {
        color: rgba(255, 255, 255, 0.4);
    }
    
    .stTabs > div > div > div > div[aria-selected="false"]:hover {
        color: rgba(255, 255, 255, 0.7);
    }
    
    .info-box {
        background: rgba(255, 255, 255, 0.02);
        border-left: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(20px);
        animation: fadeInLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .info-box:hover {
        background: rgba(255, 255, 255, 0.03);
        border-left-color: rgba(255, 255, 255, 0.3);
        transform: translateX(4px);
    }
    
    .success-box {
        background: rgba(255, 255, 255, 0.02);
        border-left: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(20px);
        animation: fadeInLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .error-box {
        background: rgba(255, 255, 255, 0.02);
        border-left: 2px solid rgba(255, 100, 100, 0.5);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(20px);
        animation: fadeInLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes progressBar {
        from {
            width: 0%;
        }
    }
    
    @keyframes shimmer {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    
    @keyframes shimmerProgress {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    @keyframes expandLine {
        from {
            width: 0;
            opacity: 0;
        }
        to {
            width: 80px;
            opacity: 1;
        }
    }
    
    .stDataFrame {
        background: rgba(255, 255, 255, 0.01);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(20px);
    }
    
    .stSpinner > div {
        border-color: rgba(255, 255, 255, 0.2) transparent transparent transparent;
        border-width: 3px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        transition: background 0.3s;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    
    h2:nth-child(1) { animation-delay: 0.1s; }
    h2:nth-child(2) { animation-delay: 0.2s; }
    h2:nth-child(3) { animation-delay: 0.3s;     }
    
    a {
        color: rgba(255, 255, 255, 0.7);
        text-decoration: none;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
    }
    
    a::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 0;
        height: 1px;
        background: rgba(255, 255, 255, 0.5);
        transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    a:hover {
        color: rgba(255, 255, 255, 1);
    }
    
    a:hover::after {
        width: 100%;
    }
    
    .stMarkdown strong {
        color: #ffffff;
        font-weight: 500;
    }
    
    .stMarkdown code {
        background: rgba(255, 255, 255, 0.05);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9em;
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Plotly Chart Animations and Hover Effects */
    .js-plotly-plot {
        transition: transform 0.2s ease;
        filter: drop-shadow(0 0 8px rgba(144, 175, 197, 0.08));
    }
    
    .js-plotly-plot:hover {
        transform: translateY(-2px);
        filter: drop-shadow(0 0 16px rgba(144, 175, 197, 0.15));
    }
    
    .plotly .bar,
    .plotly .slice {
        transition: transform 0.2s ease, filter 0.2s ease;
    }
    
    .plotly .bar:hover,
    .plotly .slice:hover {
        transform: scale(1.02);
        filter: brightness(1.1);
    }
    
    .plotly .gridlayer path {
        stroke-dasharray: none;
        opacity: 0.25;
    }
    
    .plotly .xaxislayer-above path,
    .plotly .yaxislayer-above path {
        stroke-width: 0;
    }
    
    .plotly .point {
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .plotly .point:hover {
        filter: brightness(1.3);
        transform: scale(1.2);
    }
    
    .plotly .hoverlayer {
        display: none !important;
        pointer-events: none;
    }
    
    .plotly .hovertext {
        display: none !important;
    }
    
    .plotly .modebar {
        background: rgba(42, 49, 50, 0.9) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(144, 175, 197, 0.2) !important;
    }
    
    .plotly .modebar-btn {
        color: #90AFC5 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    .plotly .modebar-btn:hover {
        background: rgba(144, 175, 197, 0.25) !important;
        transform: scale(1.15) rotate(5deg);
        filter: brightness(1.2);
    }
</style>
""", unsafe_allow_html=True)


_available_model_cache = None

def get_available_gemini_model():
    """Get the first available Gemini model by listing available models"""
    global _available_model_cache
    
    # Always check fresh (don't use cache for now)
    _available_model_cache = None
    
    try:
        # First, try to list available models
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name
                # Extract just the model name (remove 'models/' prefix if present)
                if '/' in model_name:
                    model_name = model_name.split('/')[-1]
                # Skip preview/experimental models that might have issues
                if 'preview' not in model_name.lower() and 'exp' not in model_name.lower():
                    _available_model_cache = model_name
                    return model_name
    except Exception as e:
        pass
    
    # Fallback: try common stable model names (prioritize gemini-2.5-flash which we know works)
    model_names = [
        'gemini-2.5-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
        'gemini-1.5-flash-002',
        'gemini-1.5-pro-002',
    ]
    
    # Try each model to see which one works
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            # Quick test
            test_response = model.generate_content("test")
            _available_model_cache = model_name
            return model_name
        except:
            continue
    
    return None


def generate_gemini_advice_blunders(forkCount, hangingCount, otherCount, pinCount):
    prompt = f"""
    You are a chess coach, give advice to the user based on the following data about their blunders:
    - Blunders regarding forks: {forkCount} times.
    - Blunders regarding hanging pieces: {hangingCount} times.
    - Blunders regarding missed tactics and positional errors: {otherCount} times.
    - Blunders regarding pins and skewers: {pinCount} times.

    Provide actionable advice focusing on common patterns for these types of blunders. Be concise and encouraging.
    """
    
    model_name = get_available_gemini_model()
    if not model_name:
        return "GEMINI ERROR: No available models found. Please check your API key permissions."
    
    # Try with retry logic for quota errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a quota error
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:
                    # Extract retry delay if available
                    import re
                    delay_match = re.search(r'retry.*?(\d+)', error_str, re.IGNORECASE)
                    delay = int(delay_match.group(1)) if delay_match else (attempt + 1) * 5
                    time.sleep(min(delay, 30))  # Cap at 30 seconds
                    continue
                else:
                    return f"GEMINI QUOTA ERROR: You've exceeded your free tier quota. Please wait a few minutes or upgrade your API plan. Error: {error_str[:200]}"
            
            # Try a different model if available
            if attempt < max_retries - 1:
                try:
                    # Try to get a different model
                    all_models = []
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            model_n = m.name.split('/')[-1] if '/' in m.name else m.name
                            if model_n != model_name:
                                all_models.append(model_n)
                    
                    if all_models:
                        model_name = all_models[0]
                        continue
                except:
                    pass
            
            return f"GEMINI ERROR: Failed with model {model_name}: {error_str[:200]}"
    
    return f"GEMINI ERROR: Failed after {max_retries} attempts with model {model_name}"


def get_cp_value(evaluation):
    if evaluation is None:
        return 0
    if evaluation['type'] == 'cp':
        return evaluation['value']
    elif evaluation['type'] == 'mate':
        return 100000 * (1 if evaluation['value'] > 0 else -1)
    return 0


def classify_blunder(blunder_row, stockfish_engine):
    blunder_type = "Positional/Other Blunder"
    board_after_blunder = chess.Board(blunder_row['FEN_After_Blunder'])
    blundering_player_color = chess.WHITE if blunder_row['Player_Who_Blundered'] == 'White' else chess.BLACK

    if abs(blunder_row['Eval_After_Blunder_CP']) >= 50000:
        return "Checkmate Blunder"
    try:
        stockfish_engine.set_fen_position(board_after_blunder.fen())
        opponent_best_moves = stockfish_engine.get_top_moves(3)
        for move_info in opponent_best_moves:
            opponent_best_move_uci = move_info['Move']
            if opponent_best_move_uci:
                opponent_best_move = chess.Move.from_uci(opponent_best_move_uci)
                temp_board_after_opponent_move = board_after_blunder.copy()
                if opponent_best_move in temp_board_after_opponent_move.legal_moves:
                    if board_after_blunder.is_capture(opponent_best_move):
                        captured_piece_square = opponent_best_move.to_square
                        captured_piece = board_after_blunder.piece_at(captured_piece_square)
                        if captured_piece and captured_piece.color == blundering_player_color and captured_piece.piece_type != chess.KING:
                            if not board_after_blunder.attackers(blundering_player_color, captured_piece_square):
                                return "Hanging Piece"

                    temp_board_after_opponent_move.push(opponent_best_move)

                    forking_piece_square = opponent_best_move.to_square
                    attacked_valuable_pieces_count = 0
                    for attacked_square in temp_board_after_opponent_move.attacks(forking_piece_square):
                        attacked_piece = temp_board_after_opponent_move.piece_at(attacked_square)
                        if attacked_piece and attacked_piece.color == blundering_player_color and \
                                attacked_piece.piece_type not in [chess.PAWN, chess.KING]:
                            attacked_valuable_pieces_count += 1
                    if attacked_valuable_pieces_count >= 2:
                        return "Fork Blunder"

        for square, piece in board_after_blunder.piece_map().items():
            if piece and piece.color == blundering_player_color:
                if board_after_blunder.is_pinned(blundering_player_color, square):
                    return "Pin/Skewer Blunder"
    except (ValueError, Exception):
        pass
    return blunder_type


def analyze_blunders(games_data, username, stockfish_engine):
    st.markdown(f"<h2>Blunder Analysis</h2>", unsafe_allow_html=True)
    st.markdown(f'<p style="color: rgba(255, 255, 255, 0.5); margin-bottom: 3rem; font-size: 1.1rem; font-weight: 300;">Analyzing games for <span style="color: rgba(255, 255, 255, 0.8);">{username}</span></p>', unsafe_allow_html=True)
    
    blunders_found = []
    BLUNDER_CP_THRESHOLD = 50
    
    progress_container = st.container()
    with progress_container:
        my_bar = st.progress(0, text="Analyzing game moves for blunders...")

    for game_idx, game_info in enumerate(games_data):
        board = chess.Board()
        stockfish_engine.set_fen_position(board.fen())
        prev_cp_value = get_cp_value(stockfish_engine.get_evaluation())
        for move_num, move_uci in enumerate(game_info['Moves_UCI'], 1):
            try:
                move = chess.Move.from_uci(move_uci)
                player_to_move = "White" if board.turn == chess.WHITE else "Black"
                fen_before_move = board.fen()
                if move in board.legal_moves:
                    board.push(move)
                    fen_after_move = board.fen()
                    stockfish_engine.set_fen_position(fen_after_move)
                    current_cp_value = get_cp_value(stockfish_engine.get_evaluation())
                    cp_change = prev_cp_value - current_cp_value
                    is_blunder, centipawn_loss = False, 0
                    if player_to_move == "White":
                        if cp_change > BLUNDER_CP_THRESHOLD:
                            is_blunder, centipawn_loss = True, cp_change
                    else:
                        if cp_change < -BLUNDER_CP_THRESHOLD:
                            is_blunder, centipawn_loss = True, abs(cp_change)
                    if is_blunder:
                        blunders_found.append({
                            'Game_Index': game_idx, 'Event': game_info['Event'], 'Site': game_info['Site'],
                            'Date': game_info['Date'], 'White': game_info['White'], 'Black': game_info['Black'],
                            'Result': game_info['Result'], 'Move_Number': move_num,
                            'Player_Who_Blundered': player_to_move, 'Move_UCI': move_uci,
                            'FEN_Before_Blunder': fen_before_move, 'FEN_After_Blunder': fen_after_move,
                            'Eval_Before_Blunder_CP': prev_cp_value, 'Eval_After_Blunder_CP': current_cp_value,
                            'Centipawn_Loss': centipawn_loss
                        })
                    prev_cp_value = current_cp_value
                else:
                    break
            except (ValueError, Exception):
                break
        my_bar.progress((game_idx + 1) / len(games_data), text=f"Analyzing game {game_idx + 1}/{len(games_data)}")

    my_bar.empty()
    st.markdown('<div class="success-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-weight: 400;">Analysis complete</p></div>', unsafe_allow_html=True)
    
    blunders_df = pd.DataFrame(blunders_found)
    if not blunders_df.empty:
        st.markdown('<p style="color: rgba(255, 255, 255, 0.5); margin: 2rem 0 1rem 0; font-weight: 300;">Classifying blunder types...</p>', unsafe_allow_html=True)
        blunders_df['Blunder_Type'] = blunders_df.apply(lambda row: classify_blunder(row, stockfish_engine), axis=1)
        blunders_df['Move_Number_Display'] = np.ceil(blunders_df['Move_Number'] / 2).astype(int)
        user_blunders_df = blunders_df[
            ((blunders_df['White'].str.lower() == username) & (blunders_df['Player_Who_Blundered'] == 'White')) | (
                        (blunders_df['Black'].str.lower() == username) & (
                            blunders_df['Player_Who_Blundered'] == 'Black'))]
    else:
        user_blunders_df = pd.DataFrame()

    if not user_blunders_df.empty:
        st.markdown("<h3>Game-by-Game Blunder Details</h3>", unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(255, 255, 255, 0.4); font-size: 0.9rem; margin-bottom: 2rem; font-weight: 300;">Games where blunders were found</p>', unsafe_allow_html=True)
        unique_game_indices = user_blunders_df['Game_Index'].unique()
        games_data_map = {game['game_index']: game for game in games_data}
        for game_idx in unique_game_indices:
            game_info = games_data_map.get(game_idx)
            if not game_info: continue
            game_blunders = user_blunders_df[user_blunders_df['Game_Index'] == game_idx].copy()
            game_board = chess.Board()
            for move_uci in game_info['Moves_UCI']:
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in game_board.legal_moves:
                        game_board.push(move)
                    else:
                        break
                except ValueError:
                    break
            board_svg = chess.svg.board(board=game_board, size=300)
            with st.expander(
                    f"Game {game_idx + 1}: {game_info['White']} vs. {game_info['Black']} — {game_info['Result']}"):
                game_url = game_info['Site']
                if game_url and "chess.com" in game_url:
                    st.markdown(f'<a href="{game_url}" style="color: rgba(255, 255, 255, 0.7); text-decoration: none; font-weight: 400;">View Game on Chess.com →</a>', unsafe_allow_html=True)
                col_board, col_details = st.columns([0.4, 0.6])
                with col_board:
                    st.markdown(board_svg, unsafe_allow_html=True)
                with col_details:
                    st.markdown(f"**Event:** {game_info['Event']}")
                    st.markdown(f"**White:** {game_info['White']} | **Black:** {game_info['Black']}")
                    st.markdown(f"**Result:** {game_info['Result']}")
                    st.markdown(f"**Total Moves:** {len(game_info['Moves_UCI'])}")
                st.markdown("---")
                st.markdown(f"**Blunders by {username} in this game:**")
                display_df = game_blunders[['Move_Number_Display', 'Move_UCI', 'Centipawn_Loss', 'Blunder_Type']].copy()
                display_df.rename(
                    columns={'Move_Number_Display': 'Move Number', 'Move_UCI': 'Move', 'Centipawn_Loss': 'CP Loss',
                             'Blunder_Type': 'Type'}, inplace=True)
                st.dataframe(display_df.style.set_properties(**{'font-size': '12px'}), hide_index=True)
    else:
        st.markdown(f'<div class="info-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">No blunders specifically attributed to "{username}" found in these games.</p></div>', unsafe_allow_html=True)

    if not user_blunders_df.empty:
        fork_count = (user_blunders_df['Blunder_Type'] == "Fork Blunder").sum()
        hanging_count = (user_blunders_df['Blunder_Type'] == "Hanging Piece").sum()
        other_count = (user_blunders_df['Blunder_Type'] == "Positional/Other Blunder").sum()
        pin_count = (user_blunders_df['Blunder_Type'] == "Pin/Skewer Blunder").sum()
        checkmate_blunder_count = (user_blunders_df['Blunder_Type'] == "Checkmate Blunder").sum()
        
        st.markdown("<h3>Blunder Summary</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label="Forks", value=fork_count)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label="Hanging Pieces", value=hanging_count)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label="Pins/Skewers", value=pin_count)
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label="Positional/Other", value=other_count)
            st.markdown('</div>', unsafe_allow_html=True)
        with col5:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label="Checkmate Blunders", value=checkmate_blunder_count)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # NEW FEATURE: Blunder Heatmap by Move Number
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3>Blunder Heatmap by Move Number</h3>", unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(255, 255, 255, 0.5); margin-bottom: 1rem; font-weight: 300;">When do you blunder most often?</p>', unsafe_allow_html=True)
        
        move_heatmap = user_blunders_df.groupby('Move_Number_Display').size().reset_index(name='Blunder_Count')
        move_heatmap = move_heatmap.sort_values('Move_Number_Display')
        
        colors_heatmap = ['#90AFC5', '#336B87', '#763626', '#90AFC5', '#336B87']
        fig_heatmap = go.Figure()
        fig_heatmap.add_trace(go.Bar(
            x=move_heatmap['Move_Number_Display'],
            y=move_heatmap['Blunder_Count'],
            marker=dict(
                color=[colors_heatmap[i % len(colors_heatmap)] for i in range(len(move_heatmap))],
                line=dict(width=0),
                opacity=0.85,
                pattern=dict(shape="", fillmode="overlay")
            ),
            text=move_heatmap['Blunder_Count'],
            textposition='outside',
            textfont=dict(color='#90AFC5', size=12),
            hovertemplate='<b>Move %{x}</b><br>Blunders: %{y}<br><extra></extra>',
            name='Blunders',
            showlegend=False
        ))
        fig_heatmap.update_layout(
            title=dict(text='Blunders by Move Number', font=dict(size=20, color='#90AFC5', family='Inter')),
            xaxis=dict(
                title=dict(text='Move Number', font=dict(color='#90AFC5', size=14)),
                tickfont=dict(color='#90AFC5', size=12),
                gridcolor='rgba(144, 175, 197, 0.08)',
                showgrid=True,
                showline=False,
                zeroline=False
            ),
            yaxis=dict(
                title=dict(text='Number of Blunders', font=dict(color='#90AFC5', size=14)),
                tickfont=dict(color='#90AFC5', size=12),
                gridcolor='rgba(144, 175, 197, 0.08)',
                showgrid=True,
                showline=False,
                zeroline=False
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            height=500,
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(42, 49, 50, 0.95)', font_size=12, font_family='Inter', bordercolor='rgba(144, 175, 197, 0.3)'),
            transition=dict(duration=800, easing='cubic-in-out')
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # NEW FEATURE: Blunder Type Distribution Pie Chart
        st.markdown("<h3>Blunder Type Distribution</h3>", unsafe_allow_html=True)
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            blunder_types = ['Forks', 'Hanging Pieces', 'Pins/Skewers', 'Positional/Other', 'Checkmate']
            blunder_counts = [fork_count, hanging_count, pin_count, other_count, checkmate_blunder_count]
            colors_pie = ['#90AFC5', '#336B87', '#763626', '#90AFC5', '#2A3132']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=blunder_types,
                values=blunder_counts,
                hole=0.5,
                marker=dict(
                    colors=colors_pie,
                    line=dict(width=0),
                    pattern=dict(shape="", fillmode="overlay")
                ),
                textinfo='label+percent',
                textfont=dict(size=12, color='#90AFC5', family='Inter'),
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                pull=[0.1] * len(blunder_types),
                rotation=90
            )])
            fig_pie.update_layout(
                title=dict(text='Blunder Distribution', font=dict(size=18, color='#90AFC5', family='Inter')),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                height=450,
                showlegend=True,
                legend=dict(font=dict(color='#90AFC5', size=11), bgcolor='rgba(0,0,0,0)', bordercolor='rgba(144, 175, 197, 0.2)'),
                hoverlabel=dict(bgcolor='rgba(42, 49, 50, 0.95)', font_size=12, font_family='Inter', font_color='#90AFC5', bordercolor='rgba(144, 175, 197, 0.3)'),
                transition=dict(duration=1000, easing='elastic-in-out')
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_chart2:
            # Average Centipawn Loss by Blunder Type
            avg_cp_loss = user_blunders_df.groupby('Blunder_Type')['Centipawn_Loss'].mean().reset_index()
            avg_cp_loss = avg_cp_loss.sort_values('Centipawn_Loss', ascending=False)
            
            colors_bar = ['#90AFC5', '#336B87', '#763626', '#90AFC5', '#2A3132']
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=avg_cp_loss['Blunder_Type'],
                x=avg_cp_loss['Centipawn_Loss'],
                orientation='h',
                marker=dict(
                    color=[colors_bar[i % len(colors_bar)] for i in range(len(avg_cp_loss))],
                    line=dict(width=0),
                    opacity=0.85,
                    pattern=dict(shape="", fillmode="overlay")
                ),
                text=[f'{val:.0f}' for val in avg_cp_loss['Centipawn_Loss']],
                textposition='outside',
                textfont=dict(color='#90AFC5', size=11),
                hovertemplate='<b>%{y}</b><br>Average CP Loss: %{x:.0f}<extra></extra>',
                name='CP Loss',
                showlegend=False
            ))
            fig_bar.update_layout(
                title=dict(text='Average CP Loss by Blunder Type', font=dict(size=18, color='#90AFC5', family='Inter')),
                xaxis=dict(
                    title=dict(text='Average Centipawn Loss', font=dict(color='#90AFC5', size=14)),
                    tickfont=dict(color='#90AFC5', size=12),
                    gridcolor='rgba(144, 175, 197, 0.08)',
                    showgrid=True,
                    showline=False,
                    zeroline=False
                ),
                yaxis=dict(title='', tickfont=dict(color='#90AFC5', size=12), showline=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                height=450,
                hovermode='y unified',
                hoverlabel=dict(bgcolor='rgba(42, 49, 50, 0.95)', font_size=12, font_family='Inter', font_color='#90AFC5', bordercolor='rgba(144, 175, 197, 0.3)'),
                transition=dict(duration=800, easing='cubic-in-out')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3>Chess Coach Advice</h3>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="stContainer">', unsafe_allow_html=True)
            advice = generate_gemini_advice_blunders(fork_count, hanging_count, other_count, pin_count)
            st.markdown(advice)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # NEW FEATURE: Export Blunder Data
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3>Export Data</h3>", unsafe_allow_html=True)
        csv = user_blunders_df.to_csv(index=False)
        st.download_button(
            label="Download Blunder Analysis CSV",
            data=csv,
            file_name=f"chess_blunders_{username}_{time.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def get_json_from_url(url, max_retries=3):
    """Fetch JSON from Chess.com API using requests library (much faster and more reliable than Selenium)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept': 'application/json'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.markdown(f'<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.7);">User not found or no public games available.</p></div>', unsafe_allow_html=True)
                return None
            elif e.response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
            else:
                st.markdown(f'<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.7);">HTTP Error {e.response.status_code}: {str(e)[:200]}</p></div>', unsafe_allow_html=True)
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            else:
                st.markdown(f'<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.7);">Error loading {url}: {str(e)[:200]}</p></div>', unsafe_allow_html=True)
                return None
    return None


def generate_gemini_advice_openings(opening_full_name, stats, rating, example_moves):
    prompt = f"""
    You're a chess coach. Here's a player's performance in the opening "{opening_full_name}":

    - Games Played: {stats['games']}
    - Wins: {stats['wins']}
    - Losses: {stats['losses']}
    - Draws: {stats['draws']}
    - Approximate Rating: {rating}
    - Example Opening Sequence: {example_moves}

    Based on this data, provide personalized advice.
    - If performance is poor, focus on tips to improve, common traps, or mistakes.
    - If performance is good, suggest ways to deepen their understanding, introduce key strategic plans, or mention related variations to explore.
    Give 1-2 concise action steps and be encouraging.
    """
    
    model_name = get_available_gemini_model()
    if not model_name:
        return "GEMINI ERROR: No available models found. Please check your API key permissions."
    
    # Try with retry logic for quota errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a quota error
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:
                    # Extract retry delay if available
                    import re
                    delay_match = re.search(r'retry.*?(\d+)', error_str, re.IGNORECASE)
                    delay = int(delay_match.group(1)) if delay_match else (attempt + 1) * 5
                    time.sleep(min(delay, 30))  # Cap at 30 seconds
                    continue
                else:
                    return f"GEMINI QUOTA ERROR: You've exceeded your free tier quota. Please wait a few minutes or upgrade your API plan. Error: {error_str[:200]}"
            
            # Try a different model if available
            if attempt < max_retries - 1:
                try:
                    # Try to get a different model
                    all_models = []
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            model_n = m.name.split('/')[-1] if '/' in m.name else m.name
                            if model_n != model_name:
                                all_models.append(model_n)
                    
                    if all_models:
                        model_name = all_models[0]
                        continue
                except:
                    pass
            
            return f"GEMINI ERROR: Failed with model {model_name}: {error_str[:200]}"
    
    return f"GEMINI ERROR: Failed after {max_retries} attempts with model {model_name}"


def analyze_openings(games, player_username):
    grouped_openings = {}
    player_wins, player_losses, player_draws = 0, 0, 0
    processed_games_count = 0
    player_rating = 0

    opening_groups = {
        "Sicilian Defense": ["Sicilian"],
        "Indian Game": ["Indian", "Grünfeld", "Benoni", "Benko", "Catalan"],
        "French Defense": ["French"],
        "Caro-Kann Defense": ["Caro-Kann"],
        "Queen's Gambit": ["Queen's Gambit", "Slav", "Albin", "Chigorin", "Tarrasch Defense"],
        "Queen's Pawn Opening": ["Queen's Pawn"],
        "Ruy Lopez": ["Ruy Lopez", "Spanish"],
        "Italian Game": ["Italian Game", "Giuoco Piano", "Evans Gambit"],
        "King's Pawn Opening": ["King's Pawn", "Philidor", "Petrov", "Scotch", "Vienna", "Latvian Gambit",
                                "Bishop's Opening"],
        "Four Knights Game": ["Four Knights"],
        "Scandinavian Defense": ["Scandinavian", "Center Counter"],
        "Alekhine's Defense": ["Alekhine"],
        "Pirc Defense": ["Pirc"],
        "Modern Defense": ["Modern"],
        "English Opening": ["English"],
        "Reti Opening": ["Reti"],
        "Nimzowitsch-Larsen Attack": ["Larsen", "Nimzowitsch-Larsen"],
    }
    group_order = [
        "Queen's Gambit", "Queen's Pawn Opening", "Sicilian Defense", "Indian Game", "French Defense",
        "Caro-Kann Defense",
        "Ruy Lopez", "Italian Game", "Four Knights Game", "Scandinavian Defense", "Alekhine's Defense",
        "Pirc Defense", "Modern Defense", "King's Pawn Opening", "English Opening", "Reti Opening",
        "Nimzowitsch-Larsen Attack"
    ]

    for game in games:
        white, black = game.get("white", {}), game.get("black", {})
        player_outcome = "unknown"

        if white.get("username", "").lower() == player_username:
            player_rating = white.get("rating", player_rating)
            player_outcome = white.get("result")
        elif black.get("username", "").lower() == player_username:
            player_rating = black.get("rating", player_rating)
            player_outcome = black.get("result")
        else:
            continue

        processed_games_count += 1

        final_opening_name = "Unknown Opening"
        eco_url = game.get("eco")
        pgn_str = game.get("pgn", "")

        if eco_url and "chess.com/openings" in eco_url:
            match = re.search(r'chess\.com/openings/([^/?]+)', eco_url)
            if match:
                raw_name_part = match.group(1).replace('_', ' ').replace('-', ' ')
                final_opening_name = ' '.join(word.capitalize() for word in raw_name_part.split())
        elif pgn_str:
            pgn_io = io.StringIO(pgn_str)
            try:
                pgn_game = chess.pgn.read_game(pgn_io)
                if pgn_game:
                    pgn_eco_url = pgn_game.headers.get("ECOUrl")
                    if pgn_eco_url and "chess.com/openings" in pgn_eco_url:
                        match = re.search(r'chess\.com/openings/([^/?]+)', pgn_eco_url)
                        if match:
                            raw_name_part = match.group(1).replace('_', ' ').replace('-', ' ')
                            final_opening_name = ' '.join(word.capitalize() for word in raw_name_part.split())
                    else:
                        final_opening_name = pgn_game.headers.get("Opening", "Unknown Opening")
            except Exception:
                pass

        loss_outcomes = ["lose", "resigned", "timeout", "abandoned", "checkmated", "disconnected"]
        draw_outcomes = ["draw", "agreed", "repetition", "stalemate", "insufficientmaterial", "50move"]

        main_opening_key = None
        normalized_final_name = final_opening_name.lower().replace("'", "")

        for group_name in group_order:
            normalized_keywords = [kw.lower().replace("'", "") for kw in opening_groups[group_name]]
            if any(kw in normalized_final_name for kw in normalized_keywords):
                main_opening_key = group_name
                break

        if not main_opening_key:
            if final_opening_name.lower() in ["undefined", "unknown opening"]:
                main_opening_key = "Unclassified Opening"
            else:
                main_opening_key = final_opening_name

        specific_variation_name = final_opening_name if main_opening_key != final_opening_name else "Main Line"

        if main_opening_key not in grouped_openings:
            grouped_openings[main_opening_key] = {"total_games": 0, "total_wins": 0, "total_losses": 0,
                                                  "total_draws": 0, "variations": {}}

        stats = grouped_openings[main_opening_key]
        stats["total_games"] += 1
        if player_outcome == "win":
            stats["total_wins"] += 1;
            player_wins += 1
        elif player_outcome in loss_outcomes:
            stats["total_losses"] += 1;
            player_losses += 1
        elif player_outcome in draw_outcomes:
            stats["total_draws"] += 1;
            player_draws += 1

        if specific_variation_name not in stats["variations"]:
            stats["variations"][specific_variation_name] = {"name": final_opening_name, "games": 0, "wins": 0,
                                                            "losses": 0, "draws": 0}

        var_stats = stats["variations"][specific_variation_name]
        var_stats["games"] += 1
        if player_outcome == "win":
            var_stats["wins"] += 1
        elif player_outcome in loss_outcomes:
            var_stats["losses"] += 1
        elif player_outcome in draw_outcomes:
            var_stats["draws"] += 1

    st.markdown(f"<h2>Player Summary</h2>", unsafe_allow_html=True)
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    
    with col_sum1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Games", processed_games_count)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_sum2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Wins", player_wins)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_sum3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Losses", player_losses)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_sum4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Draws", player_draws)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="info-box" style="margin-top: 2rem;"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">Estimated Rating: <strong style="color: rgba(255, 255, 255, 0.9); font-weight: 400;">{player_rating}</strong></p></div>', unsafe_allow_html=True)
    
    # NEW FEATURE: Win Rate Visualization
    if processed_games_count > 0:
        win_rate = (player_wins / processed_games_count) * 100
        st.markdown("<h3>Overall Performance</h3>", unsafe_allow_html=True)
        
        # Win/Loss/Draw Pie Chart - Bigger and Centered
        outcomes = ['Wins', 'Losses', 'Draws']
        outcome_counts = [player_wins, player_losses, player_draws]
        colors_outcome = ['#90AFC5', '#336B87', '#763626']
        
        fig_outcome = go.Figure(data=[go.Pie(
            labels=outcomes,
            values=outcome_counts,
            hole=0.5,
            marker=dict(
                colors=colors_outcome,
                line=dict(width=0),
                pattern=dict(shape="", fillmode="overlay")
            ),
            textinfo='label+percent',
            textfont=dict(size=16, color='#90AFC5', family='Inter'),
            hovertemplate='',
            hoverinfo='none',
            pull=[0.15, 0.15, 0.15],
            rotation=90
        )])
        fig_outcome.update_layout(
            title=dict(text=f'Game Outcomes (Win Rate: {win_rate:.1f}%)', font=dict(size=24, color='#90AFC5', family='Inter')),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            height=700,
            showlegend=True,
            legend=dict(font=dict(color='#90AFC5', size=14), bgcolor='rgba(0,0,0,0)', bordercolor='rgba(144, 175, 197, 0.2)', x=0.5, xanchor='center', y=-0.1, yanchor='top', orientation='h'),
            hovermode=False,
            transition=dict(duration=1000, easing='elastic-in-out')
        )
        st.plotly_chart(fig_outcome, use_container_width=True)
    
    st.markdown("<h2>Opening Repertoire</h2>", unsafe_allow_html=True)
    if not grouped_openings:
        st.markdown('<div class="info-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">No openings identified for detailed breakdown.</p></div>', unsafe_allow_html=True)
        return

    # NEW FEATURE: Opening Performance Chart
    if grouped_openings:
        st.markdown("<h3>Opening Performance Overview</h3>", unsafe_allow_html=True)
        opening_names = []
        win_rates = []
        game_counts = []
        
        for main_op_name, main_op_data in sorted(grouped_openings.items(), key=lambda item: item[1]["total_games"], reverse=True)[:10]:
            if main_op_data['total_games'] > 0:
                opening_names.append(main_op_name[:20] + '...' if len(main_op_name) > 20 else main_op_name)
                win_rate_op = (main_op_data['total_wins'] / main_op_data['total_games']) * 100
                win_rates.append(win_rate_op)
                game_counts.append(main_op_data['total_games'])
        
        if opening_names:
            fig_opening = go.Figure()
            colors_opening = ['#90AFC5' if wr >= 50 else '#763626' for wr in win_rates]
            hover_texts = [f'<b>{name}</b><br>Win Rate: {wr:.1f}%<br>Games: {gc}' 
                          for name, wr, gc in zip(opening_names, win_rates, game_counts)]
            
            fig_opening.add_trace(go.Bar(
                y=opening_names,
                x=win_rates,
                orientation='h',
                marker=dict(
                    color=colors_opening,
                    line=dict(width=0),
                    opacity=0.85,
                    pattern=dict(shape="", fillmode="overlay"),
                    cornerradius=8
                ),
                text=[f'{wr:.1f}% ({gc})' for wr, gc in zip(win_rates, game_counts)],
                textposition='outside',
                textfont=dict(color='#90AFC5', size=11),
                hovertemplate='',
                hoverinfo='none',
                name='Win Rate',
                showlegend=False
            ))
            fig_opening.update_layout(
                title=dict(text='Top Openings by Win Rate', font=dict(size=20, color='#90AFC5', family='Inter')),
                xaxis=dict(
                    title=dict(text='Win Rate (%)', font=dict(color='#90AFC5', size=14)),
                    tickfont=dict(color='#90AFC5', size=12),
                    gridcolor='rgba(144, 175, 197, 0.08)',
                    showgrid=True,
                    showline=False,
                    zeroline=False
                ),
                yaxis=dict(title='', tickfont=dict(color='#90AFC5', size=12), showline=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                height=600,
                hovermode=False,
                transition=dict(duration=800, easing='cubic-in-out')
            )
            st.plotly_chart(fig_opening, use_container_width=True)
    
    sorted_main_openings = sorted(grouped_openings.items(), key=lambda item: item[1]["total_games"], reverse=True)
    for main_op_name, main_op_data in sorted_main_openings:
        with st.expander(f"**{main_op_name}** ({main_op_data['total_games']} games)", expanded=False):
            st.markdown(f"**Overall performance for {main_op_name}:**")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Games", main_op_data['total_games'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col_m2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Wins", main_op_data['total_wins'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col_m3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Losses", main_op_data['total_losses'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col_m4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Draws", main_op_data['total_draws'])
                st.markdown('</div>', unsafe_allow_html=True)
            if main_op_data['variations']:
                st.markdown("---")
                st.markdown("**Specific variations played:**")
                sorted_variations = sorted(main_op_data['variations'].items(), key=lambda item: item[1]['games'],
                                           reverse=True)
                for var_name, var_stats in sorted_variations:
                    with st.container():
                        st.markdown('<div class="stContainer">', unsafe_allow_html=True)
                        display_name = main_op_name if var_name == "Main Line" else var_name
                        st.markdown(f"**Variation:** {display_name}")
                        st.markdown(
                            f"Games: {var_stats['games']} | Wins: {var_stats['wins']} | Losses: {var_stats['losses']} | Draws: {var_stats['draws']}")

                        pgn = ""
                        for game in games:
                            if game.get('eco', '').endswith(var_stats['name'].replace(' ', '-')):
                                pgn = game.get("pgn", "")
                                break
                        if not pgn:
                            pgn = next((g.get("pgn", "") for g in games if final_opening_name == var_stats['name']), "")

                        move_sequence = ""
                        if pgn:
                            for line in pgn.splitlines():
                                line_stripped = line.strip()
                                if line_stripped and not line_stripped.startswith("["):
                                    move_sequence = line_stripped
                                    break

                        advice = generate_gemini_advice_openings(var_stats['name'], var_stats, player_rating,
                                                                 move_sequence)
                        st.markdown("---")
                        st.markdown(f"**Advice for {display_name}:**")
                        st.markdown(advice)
                        st.markdown('</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Chess Analyzer",
        page_icon="♟️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 4rem; padding-top: 2rem;">
        <h1>♟️ Chess Analyzer</h1>
        <p style="color: rgba(255, 255, 255, 0.7); font-size: 1.3rem; margin-top: 1.5rem; font-weight: 400; letter-spacing: 0.03em; background: linear-gradient(135deg, #90AFC5 0%, #336B87 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Openings & Blunders Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p style="color: rgba(255, 255, 255, 0.6); text-align: center; margin-bottom: 4rem; font-size: 1.1rem; font-weight: 300; line-height: 1.8;">Enter your Chess.com username to get personalized insights on your openings<br>and analyze your blunders with AI-powered coaching.</p>', unsafe_allow_html=True)

    engine = None
    try:
        engine = Stockfish(STOCKFISH_EXECUTABLE_PATH, parameters={"Contempt": 0, "Threads": 4, "Hash": 256})
    except Exception as e:
        st.markdown(f'<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.8);">Error initializing Stockfish engine. Please ensure the path is correct and Stockfish is installed. Error: {e}</p></div>', unsafe_allow_html=True)
        st.stop()

    st.markdown('<div style="margin-bottom: 3rem;"></div>', unsafe_allow_html=True)
    
    col_input1, col_input2 = st.columns([2, 1])
    
    with col_input1:
        username = st.text_input("Chess.com Username", key="username_input", placeholder="Enter your username").strip().lower()
    
    with col_input2:
        games_to_fetch_count = st.number_input(
            "Games to analyze",
            min_value=5,
            max_value=200,
        value=20,
        step=5,
        key="games_count_input"
    )

    st.markdown('<div style="margin-bottom: 2rem;"></div>', unsafe_allow_html=True)

    if st.button("Analyze My Games", key="analyze_button", use_container_width=True) and username:
        with st.spinner("Fetching games and analyzing... This might take a moment, especially for blunder analysis."):
            try:
                archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
                archives_data = get_json_from_url(archives_url)

                if not archives_data or "archives" not in archives_data:
                    st.markdown('<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.8);">Failed to fetch game archives. Please check the username or ensure the user has public archives.</p></div>', unsafe_allow_html=True)
                    return

                all_games = []
                progress_bar = st.progress(0, text="Fetching games...")

                archives_list = archives_data["archives"]
                archives_to_check = list(reversed(archives_list))  # newest first

                for idx, archive_url in enumerate(archives_to_check):
                    if len(all_games) >= games_to_fetch_count:
                        break

                    progress_fraction = min(1.0, len(all_games) / max(1, games_to_fetch_count))
                    progress_bar.progress(progress_fraction, text=f"Fetching games from: {archive_url.split('/')[-2]}/{archive_url.split('/')[-1]}")

                    archive_data = get_json_from_url(archive_url)
                    if archive_data and "games" in archive_data:
                        games_from_archive = archive_data["games"]
                        if games_from_archive:
                            games_from_archive = sorted(games_from_archive, key=lambda g: g.get("end_time", 0))
                            for game in games_from_archive:
                                if len(all_games) >= games_to_fetch_count:
                                    break
                                all_games.append(game)

                    time.sleep(0.1)

                progress_bar.progress(1.0, text="Finished fetching games")
                progress_bar.empty()

                if all_games:
                    recent_games = all_games[-games_to_fetch_count:]
                    blunder_analysis_games_data = []
                    for idx, game in enumerate(recent_games):
                        pgn_moves = []
                        pgn_text = game.get("pgn", "")
                        try:
                            pgn_game = chess.pgn.read_game(io.StringIO(pgn_text))
                            if pgn_game: pgn_moves = [x.uci() for x in pgn_game.mainline_moves()]
                        except Exception as e:
                            st.markdown(f'<div class="info-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">Could not parse PGN for game {idx}: {e}</p></div>', unsafe_allow_html=True)

                        event_name = game.get("time_class", "Live Game").replace("_", " ").capitalize()

                        blunder_analysis_games_data.append({
                            'game_index': idx, 'Event': event_name, 'Site': game.get("url", "N/A"),
                            'Date': game.get("end_time", "N/A"), 'White': game.get("white", {}).get("username", "N/A"),
                            'Black': game.get("black", {}).get("username", "N/A"),
                            'Result': game.get("white", {}).get("result", "N/A"), 'Moves_UCI': pgn_moves
                        })

                    st.markdown(f'<div class="success-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-weight: 400;">Successfully fetched {len(recent_games)} most recent games for analysis</p></div>', unsafe_allow_html=True)

                    tab1, tab2 = st.tabs(["Opening Analysis", "Blunder Analysis"])
                    with tab1:
                        analyze_openings(recent_games, username)
                    with tab2:
                        analyze_blunders(blunder_analysis_games_data, username, engine)
                else:
                    st.markdown('<div class="info-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">No games found for this username.</p></div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="error-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.8);">An unexpected error occurred: {e}</p></div>', unsafe_allow_html=True)
                st.markdown('<div class="info-box"><p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-weight: 300;">Common issues: Incorrect username, network problems, or temporary Chess.com API issues.</p></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
