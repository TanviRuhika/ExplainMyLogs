# Plugin Documentation – ExplainMyLogs

## 📌 What is this?

This plugin extracts logs from Fedora’s systemd journal (`journalctl`) using parameters provided in a configuration JSON file. It returns logs in a structured JSON format for analysis or processing.

---

## 🚀 How to Use

### 📁 1. Create a config file (e.g. `config.json`)

```json
{
  "log_type": "sshd",
  "log_duration": "1D"
}

ExplainMyLogs/
├── plugin/               # Contains plugin logic (__main__.py)
├── plugin                # Executable CLI script
├── config.json           # Sample config input
├── poc_demo.json         # Output log file
├── doc/plugin.md         # Plugin documentation (this file)
├── design/design.md      # Design document from proposal
├── poc_results.md        # PoC log test summary
