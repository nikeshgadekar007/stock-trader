#!/usr/bin/env python
"""Setup script for Stock Trading Analysis System"""
from setuptools import setup, find_packages

setup(
    name="stock-trader",
    version="1.0.0",
    description="Automated intraday trading system with AI-powered analysis",
    author="Nikesh Gadekar",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "streamlit-autorefresh>=1.0.0",
        "plotly>=5.18.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "yfinance>=0.2.28",
        "python-dateutil>=2.8.0",
        "requests>=2.31.0",
        "firebase-admin>=7.0.0",
        "vaderSentiment>=3.3.0",
        "textblob>=0.18.0",
        "schedule>=1.2.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "stock-trader=app:main",
        ],
    },
)