# Network Diagnostic & Monitoring Tool

A comprehensive command-line interface (CLI) application written in Python for network analysis. This tool allows users to measure internet connection speed, map latency to global servers, monitor connection stability over time, and visualize data through automatically generated charts.

## Features

*   **Global Ping Map:** Measures latency (ping) to over 30 strategic locations worldwide (Europe, Asia, Americas, and local nodes) to provide a snapshot of network connectivity.
*   **Ping Monitor:** Real-time latency tracking to a specific server for a user-defined duration. Generates a line chart to visualize jitter and stability.
*   **Speed Stability Test:** Performs multiple consecutive speed tests (Download/Upload) to analyze connection stability and potential throttling.
*   **Data Visualization:** Uses `matplotlib` to generate professional-grade dark-themed charts (Bar and Line graphs) for all tests.
*   **Auto-Open:** Automatically opens the generated report images upon test completion.
*   **Cross-Platform:** Works on Windows, macOS, and Linux.

## Prerequisites

*   Python 3.7 or higher
*   Administrator/Root privileges (required for ICMP ping on some operating systems)

## Installation

1.  Clone the repository or download the source code.
2.  Install the required dependencies using pip:

```bash
pip install -r requirements.txt
