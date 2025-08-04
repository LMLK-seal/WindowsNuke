# 🗂️ WindowsNuke Windows Remover tool for secondary Drive

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)

WindowsNuke safely remove Windows installations from secondary drives, helping you reclaim valuable storage space after system migrations.

![Application logo](https://github.com/LMLK-seal/WindowsNuke/blob/main/WindowsNukeLogo.png?raw=true)

## 🎯 Purpose

When upgrading to a larger SSD and keeping your old drive as secondary storage, the old Windows installation becomes redundant and wastes significant disk space. This tool provides a safe, controlled way to:

- 🔍 **Scan** secondary drives for Windows installations
- 📊 **Analyze** space usage of Windows-related files and folders
- 🗑️ **Remove** system files while preserving user data (with careful handling)
- 💾 **Reclaim** gigabytes of storage space

## ⚠️ Important Safety Notice

> **🚨 CRITICAL WARNING**: This tool performs irreversible file deletion operations. Always backup important data before use. The safest method for drive cleanup is manual backup followed by drive formatting.

## ✨ Features

### 🖥️ Modern GUI Interface
- **Dark Theme**: Easy on the eyes with CustomTkinter styling
- **Real-time Feedback**: Live status updates during operations
- **Detailed Results**: Comprehensive scan results with size calculations
- **Safety Prompts**: Multiple confirmation dialogs before deletion

### 🔧 Advanced Functionality
- **Administrator Privilege Check**: Ensures proper permissions for system file access
- **Multi-Drive Support**: Automatically detects non-system drives
- **Intelligent Scanning**: Identifies Windows installations via System32 detection
- **Size Calculation**: Accurate space usage analysis with GB conversion
- **Permission Handling**: Advanced file permission management using Windows tools

### 🛡️ Safety Features
- **System Drive Protection**: Automatically excludes the current Windows drive
- **Confirmation Dialogs**: Multiple verification steps before deletion
- **Error Handling**: Graceful handling of permission and access errors
- **Progress Tracking**: Real-time deletion progress with detailed logging

## 📊 Screenshot

![Application screenshoot](https://github.com/LMLK-seal/WindowsNuke/blob/main/Screenshot.jpg?raw=true)

## 🚀 Installation

### Prerequisites
```bash
# Required Python packages
pip install customtkinter psutil
```

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.7 or higher
- **Privileges**: Administrator rights required
- **Memory**: Minimal (< 50MB RAM usage)

### Quick Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/WindowsNuke.git
   cd WindowsNuke
   ```

2. **Install dependencies**:
   ```bash
   pip install customtkinter psutil
   ```

3. **Run as Administrator**:
   ```bash
   # Right-click Command Prompt -> "Run as administrator"
   python WindowsNuke.py
   ```

## 📖 Usage Guide

### Step-by-Step Process

1. **🔐 Launch with Admin Rights**
   - Right-click `WindowsNuke.py` → "Run as administrator"
   - Or run Command Prompt as admin and execute the script

2. **💿 Select Target Drive**
   - Choose your secondary drive from the dropdown menu
   - System drive (C:) is automatically excluded for safety

3. **🔍 Scan for Windows Installation**
   - Click "Scan for Windows Installation"
   - Wait for the comprehensive analysis to complete
   - Review the detailed results showing files and space usage

4. **🗑️ Execute Deletion (Optional)**
   - Review the scan results carefully
   - Click "DELETE Found Files & Folders" if satisfied
   - Confirm through multiple safety prompts
   - Monitor the real-time deletion progress

### 📁 What Gets Deleted

The tool targets these Windows-specific components:

| **Folders** | **Description** | **Typical Size** |
|-------------|-----------------|------------------|
| `Windows` | Core system files | 15-25 GB |
| `Program Files` | Installed applications | 5-50 GB |
| `Program Files (x86)` | 32-bit applications | 2-20 GB |
| `ProgramData` | Application data | 1-10 GB |
| `$Recycle.Bin` | Deleted files cache | 0.1-5 GB |
| `Users` | ⚠️ User profiles and data | Variable |

| **System Files** | **Description** |
|------------------|-----------------|
| `pagefile.sys` | Virtual memory file |
| `swapfile.sys` | Modern swap file |
| `hiberfil.sys` | Hibernation data |

## 🔧 Technical Implementation

### Architecture Overview
```
WindowsRemoverApp (CustomTkinter)
├── Drive Detection (psutil)
├── Permission Management (Windows API)
├── Threading (GUI responsiveness)
├── File Operations (shutil, os)
└── System Integration (subprocess)
```

### Key Technologies
- **🎨 GUI Framework**: CustomTkinter for modern interface
- **💽 System Access**: psutil for drive enumeration
- **🔐 Permissions**: Windows takeown/icacls commands
- **⚡ Threading**: Non-blocking UI operations
- **📊 File Operations**: Python standard library

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Code Standards
- **Style**: Follow PEP 8 guidelines
- **Documentation**: Comment complex operations
- **Safety**: Prioritize data safety in all modifications
- **Testing**: Test on non-production drives only

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Use at your own risk.** This software is provided "as-is" without warranty. The authors are not responsible for data loss or system damage. Always backup important data before use.

## 🙋‍♂️ Support

- **📧 Issues**: [GitHub Issues](https://github.com/LMLK-seal/windows-remover/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/LMLK-seal/windows-remover/discussions)
- **📖 Wiki**: [Project Wiki](https://github.com/LMLK-seal/windows-remover/wiki)

## 🎖️ Acknowledgments

- **CustomTkinter** team for the modern GUI framework
- **Python** community for excellent libraries
- **Windows** system administrators for inspiration

---

<div align="center">

**⭐ Star this repository if it helped you reclaim storage space! ⭐**

Made with ❤️ By LMLK-seal.

</div>
