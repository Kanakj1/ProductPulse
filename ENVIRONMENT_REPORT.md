# ProductPulse — Environment Inspection Report (`ENVIRONMENT_REPORT.md`)

**Date of Inspection**: 2026-10-14  
**Workspace Path**: `D:\ProductPulse-nlp-bda`  
**Inspected By**: Antigravity (Gemini 3.8 Flash)  
**Permanent Category Lock**: **Mobile Phones & Accessories**  
**Authorized Data Source**: **McAuley-Lab/Amazon-Reviews-2023** (Hugging Face)

---

## 1. Executive Summary

This report documents the empirical environment findings gathered through non-destructive, read-only inspection commands executed on the host system. No dependencies were installed, no services were started or terminated, no files were deleted, and no dataset downloads were initiated.

### Key Takeaways
1. **Core Development Tooling**: Python 3.12.2, pip 24.0, Node.js v22.20.0, npm 11.3.0, and Git 2.55.0 are installed and functional.
2. **Storage Measurement**: Measured available disk space is 185.53 GB free on drive C: (474.81 GB total) and 397.05 GB free on drive D: (454.58 GB total). Whether this capacity is adequate depends on source partition sizes and bounded sample feasibility to be established in Phase 1; capacity adequacy cannot be asserted prematurely.
3. **Container & Virtualization Runtimes**: Docker 29.3.1 (with active daemon) and WSL2 (Ubuntu and docker-desktop) are available. A pre-existing container `yogyatamitra_postgres` (port 5432) was observed and left untouched; Phase 0 started zero containers.
4. **Hadoop / Hive Feasibility**: The `hadoop` and `hive` CLI commands were **not found in the checked PATH** on either the Windows host or within WSL Ubuntu. No Hadoop/Hive daemons or Windows services were observed running. Complete system-wide absence of unconfigured binaries in arbitrary directories remains **UNVERIFIED**. Furthermore, host Java is **Java 24.0.1**. Compatibility must be established for the specific Hadoop/Hive versions selected using authoritative compatibility documentation, rather than assuming universal support or universal incompatibility. Neither Hadoop nor Hive was selected or installed in Phase 0.
5. **Port Conflicts**: Both target local development ports (**5173** and **8000**) are currently occupied by external background processes from another pre-existing project (`D:\nlp-project`). Phase 0 left these processes untouched.

---

## 2. Detailed Inspection Findings

### 2.1 Host Operating System & Hardware

| Parameter | Observed Fact | Command / Source |
| :--- | :--- | :--- |
| **OS Name** | Microsoft Windows 11 Home Single Language | `Get-CimInstance Win32_OperatingSystem` |
| **OS Version / Build** | 10.0.26200 (Build 26200, 64-bit) | `[System.Environment]::OSVersion.VersionString` |
| **CPU Model** | 12th Gen Intel(R) Core(TM) i5-1240P | `Get-CimInstance Win32_Processor` |
| **CPU Physical Packages** | 1 Socket / Package | `Get-CimInstance Win32_ComputerSystem` (`NumberOfProcessors`) |
| **CPU Physical Cores** | 12 Physical Cores | `Get-CimInstance Win32_Processor` (`NumberOfCores`) |
| **CPU Logical Processors** | 16 Logical Processors | `Get-CimInstance Win32_Processor` (`NumberOfLogicalProcessors`) |
| **Physical Memory (RAM)** | 21,126,909,952 bytes (~20.0 GB / 19.67 GiB) | `Win32_ComputerSystem.TotalPhysicalMemory` |

### 2.2 Storage & Volumes

| Drive | Volume Label | File System | Total Capacity | Free Space | Free % | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **C:** | Windows | NTFS | 474.81 GB | 185.53 GB | 39.1% | Healthy |
| **D:** | New Volume (Workspace) | NTFS | 454.58 GB | 397.05 GB | 87.3% | Healthy |

*Assessment*: Measured available free space is 397.05 GB on drive D: and 185.53 GB on drive C:. Dataset capacity adequacy cannot be asserted until source dataset size, partition volumes, and bounded access feasibility are established in Phase 1.

### 2.3 Workspace & Git Status

| Check | Result | Evidence |
| :--- | :--- | :--- |
| **Working Directory** | `D:\ProductPulse-nlp-bda` | Verified via `Get-Location` |
| **Existing Files** | 0 files prior to Phase 0 documentation | `Get-ChildItem -Force` returned empty |
| **Git Repository** | Not initialized | `git status` -> `fatal: not a git repository` |
| **Git Version** | Git 2.55.0.windows.4 | `git --version` |

### 2.4 Python Runtime & Libraries

| Component | Detected Version | Details / Path |
| :--- | :--- | :--- |
| **Python** | 3.12.2 | `C:\Users\kanak\AppData\Local\Programs\Python\Python312\python.exe` |
| **pip** | 24.0 | In Python 3.12 site-packages |
| **venv module** | Available | Built-in standard library module confirmed operational |
| **Relevant Global Packages** | - `nltk` 3.9.1<br/>- `scikit-learn` 1.3.2<br/>- `pandas` 2.1.4<br/>- `numpy` 1.26.4<br/>- `uvicorn` 0.49.0<br/>- `starlette` 1.2.1 | Identified via `pip list` |
| **Missing Python Packages** | `fastapi`, `pydantic`, `sqlalchemy` | Not found in global site-packages |

*Recommendation*: Create an isolated virtual environment (`.venv`) in later phases to manage FastAPI, Pydantic, and SQLAlchemy without polluting global Python.

### 2.5 JavaScript & Web Tooling

| Tool | Version | Status |
| :--- | :--- | :--- |
| **Node.js** | v22.20.0 | Verified (`node --version`) |
| **npm** | 11.3.0 | Verified (`npm --version`) |
| **Frontend Project** | None currently | `frontend/` directory does not yet exist |

### 2.6 Docker & WSL Virtualization

| Component | Version / Distribution | State | Observations |
| :--- | :--- | :--- | :--- |
| **Docker Engine** | 29.3.1 (build c2be9cc) | Running | Active daemon. Pre-existing container `yogyatamitra_postgres` (port 5432) was running prior to this session and was left untouched. Phase 0 started zero containers. |
| **WSL 2** | Version 2 Architecture | Active | Two distributions registered: `docker-desktop` (default) and `Ubuntu`. |

### 2.7 Big Data Analytics (Hadoop & Hive) Readiness

| Component | Host (Windows) Status | WSL (Ubuntu) Status | Assessment & Empirical Findings |
| :--- | :--- | :--- | :--- |
| **Java Runtime** | `24.0.1` (`JAVA_HOME = C:\Program Files\Java\jdk-24`) | `java: command not found` in PATH | **Observed**: Host Java is 24.0.1. Official compatibility with specific Hadoop/Hive releases must be verified using authoritative documentation prior to Phase 9. |
| **Java Compiler** | `javac 24.0.1` | Not found in PATH | Host has JDK 24. |
| **Hadoop CLI** | `hadoop: CommandNotFoundException` (not in PATH) | `hadoop: command not found` (not in PATH) | Command not found in checked PATH locations. |
| **HDFS / YARN Daemons** | 0 matching Windows services; 0 matching processes | 0 matching processes in `ps -ef` | Verified: No daemons/processes running at inspection time. Complete absence of unconfigured binaries on disk is **UNVERIFIED**. |
| **Apache Hive** | `hive: CommandNotFoundException` (not in PATH) | `hive: command not found` (not in PATH) | Command not found in checked PATH locations. |

*Process & Service Evidence*:
- Windows Services Check: `Get-Service -Name *hadoop*, *hive*, *hdfs*, *yarn* -ErrorAction SilentlyContinue` returned zero services.
- Windows Process Check: `Get-Process | Where-Object { $_.ProcessName -match "hadoop|hive|hdfs|yarn" }` returned zero processes.
- WSL Process Check: `wsl -d Ubuntu -e bash -c "ps -ef | grep -E 'hadoop|hive|hdfs|yarn' | grep -v grep"` returned zero matching processes.
- Environment Variables: Only `JAVA_HOME` is set; `HADOOP_HOME`, `HIVE_HOME`, `HDFS_CONF_DIR`, and `YARN_HOME` are absent from Windows and WSL environments.

*Assessment for Phase 9*:  
Running real Hadoop MapReduce and Hive jobs cannot currently be done on the host or in WSL Ubuntu using default PATH configurations because the `hadoop` and `hive` commands were not found in checked PATHs, and no running daemons or services were detected. Furthermore, host Java is 24.0.1; compatibility must be established for the specific Hadoop/Hive versions selected using authoritative compatibility documentation before Phase 9.  
*Potential Execution Options to Evaluate in Phase 9*:
1. Run a lightweight Dockerized Hadoop+Hive single-node container with a verified compatible JDK (Docker daemon is active).
2. Install a verified compatible JDK and Hadoop/Hive inside the existing WSL `Ubuntu` distribution.  
*Note: Neither option is implemented or verified working in Phase 0; evaluating them is marked **UNVERIFIED**. Decision and selection will be submitted for user approval prior to Phase 9.*

### 2.8 Local Port Occupancy Inspection

| Target Port | Target Service | Current Status | Owning Process PID | Process Details / Command Line | Origin & Action Taken |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **5173** | ProductPulse Frontend | **OCCUPIED** | `5988` | `node.exe` running `D:\nlp-project\frontend\node_modules\vite\bin\vite.js` | Pre-existed Phase 0. Left untouched. |
| **8000** | ProductPulse Backend | **OCCUPIED** | `40392`, `41424` | `python.exe` running `run_backend.py` / `uvicorn app.main:app` | Pre-existed Phase 0. Left untouched. |

*Action Taken*: Confirmed these external processes pre-existed this project session. No processes were killed or interrupted. Phase 0 started zero processes and stopped zero processes.  
*Recommendation*: Before launching the ProductPulse backend in Phase 4 and frontend in Phase 5, the user should gracefully stop the external `nlp-project` development servers or permit alternative local ports.

---

## 3. Commands Executed and Verification Results
 
| # | Exact Command Executed | Exit Code | Verified Output Summary | Direct Observation vs. Inference |
| :-: | :--- | :-: | :--- | :--- |
| 1 | `Get-Location; Get-ChildItem -Force` | 0 | `d:\ProductPulse-nlp-bda` returned; directory empty. | **Observed**: Empty workspace path. |
| 2 | `git status; git --version` | 0 | `fatal: not a git repository`; `git version 2.55.0.windows.4`. | **Observed**: Git 2.55.0 installed; no `.git` dir. *Note*: In PowerShell, `;` executes subcommands sequentially; `git status` failed (exit code 128), but subsequent `git --version` succeeded, masking status failure in overall return code. |
| 3 | `[System.Environment]::OSVersion.VersionString; Get-CimInstance Win32_OperatingSystem...` | 0 | Windows 11 Home Single Language (Build 26200, 64-bit). | **Observed**: Host OS version and build. |
| 4 | `python --version; py --version; pip --version` | 0 | Python 3.12.2; pip 24.0. | **Observed**: Python 3.12.2 runtime and pip 24.0 paths. |
| 5 | `python -m venv --help; pip list` | 0 | venv functional; nltk 3.9.1, scikit-learn 1.3.2 installed. | **Observed**: venv module present; installed package list. |
| 6 | `node --version; npm --version` | 0 | Node.js v22.20.0; npm 11.3.0. | **Observed**: Node and npm versions. |
| 7 | `Get-CimInstance Win32_LogicalDisk...; Get-CimInstance Win32_ComputerSystem...` | 0 | C: 185.53 GB free; D: 397.05 GB free; 20 GB RAM. | **Observed**: Disk volumes and RAM bytes. |
| 8 | `docker --version; docker ps` | 0 | Docker 29.3.1; container `yogyatamitra_postgres` on 5432. | **Observed**: Docker CLI and daemon active; container running. |
| 9 | `wsl --list --verbose` | 0 | WSL2 active: `docker-desktop` (default) and `Ubuntu`. | **Observed**: WSL2 installed; distributions registered. |
| 10 | `java -version; javac -version; hadoop version; hive --version` | 1 | Java 24.0.1 present; `hadoop` and `hive` threw CommandNotFoundException. | **Observed**: Host Java 24.0.1 is present; Hadoop and Hive are missing from Windows PATH. |
| 11 | `Get-ChildItem Env: \| Where-Object { $_.Name -match "JAVA\|HADOOP\|HIVE\|SPARK" }` | 0 | `JAVA_HOME = C:\Program Files\Java\jdk-24`; no Hadoop/Hive vars. | **Observed**: Only `JAVA_HOME` is defined on host. |
| 12 | `wsl -d Ubuntu -e bash -c "which java javac hadoop hive; ..."` | 1 | bash: java, hadoop, hive commands not found in Ubuntu WSL. | **Observed**: Java, Hadoop, Hive missing from WSL Ubuntu PATH. |
| 13 | `Get-NetTCPConnection -LocalPort 5173, 8000` | 0 | Ports 5173 and 8000 in Listen/Established state. | **Observed**: PIDs 5988, 40392, 41424 hold ports. |
| 14 | `Get-CimInstance Win32_Process -Filter "ProcessId = 5988 or ..."` | 0 | PIDs identified with specific command lines. | **Observed**: Command lines contain `D:\nlp-project`. **Inference**: An external project is actively running Vite and Uvicorn. |
| 15 | `Test-Path "PROJECT_SPEC.md", "PHASE_STATUS.md", ...` | 0 | Returned False for all 5 documents before creation. | **Observed**: None of the 5 files existed prior to creation. |
| 16 | `Get-ChildItem -Path "d:\ProductPulse-nlp-bda"` | 0 | Confirmed all 5 files successfully created. | **Observed**: 5 files present with expected non-zero sizes. |
| 17 | `Get-CimInstance Win32_Processor \| Select-Object Name, NumberOfCores, NumberOfLogicalProcessors` | 0 | 12th Gen Intel(R) Core(TM) i5-1240P; 12 cores; 16 logical processors. | **Observed**: CPU model, physical core count, and logical processor count. |
| 18 | `Get-Service -Name *hadoop*, *hive*, *hdfs*, *yarn* -ErrorAction SilentlyContinue; Get-Process \| Where-Object { $_.ProcessName -match "hadoop\|hive\|hdfs\|yarn" }` | 0 | Zero services returned; zero processes returned. | **Observed**: No Windows services or processes with Hadoop/Hive names running at inspection time. |
| 19 | `wsl -d Ubuntu -e bash -c "ps -ef \| grep -E 'hadoop\|hive\|hdfs\|yarn' \| grep -v grep"` | 1 | No matching processes returned. | **Observed**: No running processes matching Hadoop/Hive names in WSL Ubuntu. |

---

## 4. Risks, Unknowns, and Action Items for Phase 1

1. **Category Mapping Verification**: The Hugging Face repository `McAuley-Lab/Amazon-Reviews-2023` must be queried in Phase 1 to verify whether the target category is named `Cell_Phones_and_Accessories`, `Electronics`, or something else, and whether product metadata and reviews are properly linked.
2. **Selective Access Feasibility**: Phase 1 must verify whether streaming or partial range reads are supported to prevent downloading multi-gigabyte files.
3. **Port Conflict Resolution**: External servers occupy ports 5173 and 8000. These must be stopped or alternative ports explicitly approved by the user before starting servers in Phase 4 and Phase 5.
4. **Hadoop/Hive Environment Strategy**: Neither Hadoop nor Hive is working on the host or in WSL. Prior to Phase 9, an execution environment (e.g. Docker container or WSL with compatible Java) and verified version compatibility must be evaluated and approved by the user. *Unverified: Running Hadoop/Hive in Docker or WSL has not been tested or established in Phase 0.*
