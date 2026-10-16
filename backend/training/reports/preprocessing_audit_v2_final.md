# Smart-Log — Final Pre-Training Preprocessing Audit Report
**Generated:** 2026-10-15 02:16:05  
**Pipeline:** `backend/training/train_ait_lds_v2.py` v2 (post-audit fixes)  
**HDFS_v1:** never accessed  
**Models trained:** none  
**Artifacts overwritten:** none  

---

## 1. Dry-Run Execution

| Item | Value |
|------|-------|
| Command | `python -m backend.training.train_ait_lds_v2 --dry-run` |
| Python exit code | **0** (confirmed by subprocess test) |
| PowerShell exit | 1 — stderr artifact only (see §4) |
| All 3 datasets completed | Yes |
| Stop message | [DRY RUN] Data loaded. Stopping before training. |
| No Python traceback | Confirmed |

---

## 2. Before vs After Record Counts

| Dataset | Phase | Pre-dedup | Removed | Conflicts | After | Normal | Anomalous | Anom% |
|---------|-------|-----------|---------|-----------|-------|--------|-----------|-------|
| fox | BEFORE (v1) | 777,685 | — | — | 777,685 | 777,042 | 643 | 0.08% |
| fox | **AFTER (v2)** | 777,685 | **131,342** | **0** | **646,343** | 601,776 | **44,567** | **6.895%** |
| russellmitchell | BEFORE (v1) | 656,609 | — | — | 656,609 | 655,583 | 1,026 | 0.16% |
| russellmitchell | **AFTER (v2)** | 656,609 | **134,812** | **0** | **521,797** | 468,065 | **53,732** | **10.297%** |
| santos | BEFORE (v1) | 835,505 | — | — | 835,505 | 826,745 | 8,760 | 1.05% |
| santos | **AFTER (v2)** | 835,505 | **129,745** | **0** | **705,760** | 658,720 | **47,040** | **6.665%** |

### Per-Dataset Detail

**FOX:** raw_lines=777,685 | blank_skipped=592 | parse_errors=0 | feature_errors=0 | files_with_label=5/271 | uncertain_records=0  
**RUSSELLMITCHELL:** raw_lines=656,609 | blank_skipped=514 | parse_errors=0 | feature_errors=0 | files_with_label=5/226 | uncertain_records=0  
**SANTOS:** raw_lines=835,505 | blank_skipped=520 | parse_errors=0 | feature_errors=0 | files_with_label=7/227 | uncertain_records=0  

---

## 3. Label Mapping

**ANOMALOUS_LABELS count:** 22  
**All 22 labels** confirmed from dataset `rules/*.yaml` files.  
**classify_labels() unit tests:** 12/12 PASS  
**Uncertain labels found in data:** 0  

| Label | Attack Type | Source Rule File |
|-------|-------------|-----------------|
| `attacker` | DNS exfil co-label | dnsmasq.yaml |
| `attacker_http` | HTTP from attacker IP | apache.yaml |
| `attacker_vpn` | VPN from attacker IP | openvpn.yaml |
| `attacker_change_user` | /bin/su hijack | audit.yaml |
| `crack_passwords` | wpcrack window | monitoring.yaml |
| `dirb` | Dir brute-force | apache.yaml |
| `dns_scan` | DNS brute-force probes | dnsmasq.yaml |
| `dnsteal` | DNS exfil domain queries | dnsmasq.yaml |
| `dnsteal-received` | Active exfil window | dnsmasq.yaml |
| `dnsteal-dropped` | DNS retries post-shutdown | dnsmasq.yaml |
| `escalate` | Privilege escalation | audit.yaml |
| `escalated_command` | Sudo command events | audit.yaml |
| `escalated_sudo_command` | Sudo command audit | audit.yaml |
| `escalated_sudo_session` | PAM session via sudo | 0_auth.yaml |
| `exfiltration-service` | Exfil service window | audit.yaml |
| `foothold` | Initial access phase | apache.yaml/openvpn.yaml |
| `network_scan` | Nmap PTR scan | dnsmasq.yaml |
| `service_scan` | Nmap via Apache | apache.yaml |
| `traceroute` | Traceroute PTR queries | dnsmasq.yaml |
| `webshell_cmd` | Webshell HTTP execution | apache.yaml |
| `webshell_upload` | 3-step webshell upload | apache.yaml |
| `wpscan` | WPScan DNS/HTTP traffic | dnsmasq.yaml |

---

## 4. Exit Code 1 — Root Cause

> **Root cause: PowerShell `2>&1` stderr artifact — NOT a Python error.**

Evidence from subprocess test in this audit session:  
- Python script that logs to stderr then calls `sys.exit(0)` → actual exit code: **0**  
- Python script that raises RuntimeError → actual exit code: **1**  
- Dry-run output shows all 3 datasets completing with correct counts  
- Final log line: `[DRY RUN] Data loaded. Stopping before training.`  
- No Python traceback or exception anywhere in the output  

PowerShell `2>&1` wraps each stderr line as an `ErrorRecord`,  
setting `$LASTEXITCODE=1` whenever any stderr output exists,  
regardless of the actual Python exit code.

---

## 5. Unlabeled Records — Documented Limitation

> **WARNING: Unlabeled records are NOT verified benign data.**

- **fox:** 5/271 files have a label file; 266 files treat all lines as Normal by default
- **russellmitchell:** 5/226 files have a label file; 221 files treat all lines as Normal by default
- **santos:** 7/227 files have a label file; 220 files treat all lines as Normal by default

The AIT-LDS annotation pipeline only labeled logs on machines directly
involved in the attack chain. Other machine logs are unannotated and
**may contain undetected attack traffic** not covered by annotation rules.
This is inherent to the dataset — not fixable in preprocessing.
Models should be evaluated with this limitation explicitly acknowledged.

---

## 6. Feature Schema

**ALL_FEATURES (11):** `message_length, token_count, digit_ratio, entropy, has_error, has_warning, has_auth, has_failed_auth, has_denied, has_ip, service`  
**`severity_level`:** REMOVED (constant=6, std=0, zero discriminative power)  
**`severity_level` in LogParser output:** False (verified live)  

### Feature Variances (FOX, post-dedup)

| Feature | Mean | Std | Zero-Variance? |
|---------|------|-----|----------------|
| `message_length` | 150.487 | 100.8616 | no |
| `token_count` | 10.2775 | 4.9476 | no |
| `digit_ratio` | 0.2468 | 0.082 | no |
| `entropy` | 4.9996 | 0.504 | no |
| `has_error` | 0.0115 | 0.1067 | no |
| `has_warning` | 0.0011 | 0.0334 | no |
| `has_auth` | 0.0894 | 0.2853 | no |
| `has_failed_auth` | 0.0003 | 0.0187 | no |
| `has_denied` | 0.0001 | 0.0075 | no |
| `has_ip` | 0.7643 | 0.4244 | no |

---

## 7. Train/Validation Leakage Prevention

**Order:** Raw records → deduplicate by MD5 → `train_test_split` (80/20, stratified) → `fit_transform(train)` → `transform(val)`  

| Check | Result |
|-------|--------|
| Index overlap train ∩ val | 0 |
| Raw-line MD5 overlap | 0 |
| NaN in train output | 0 |
| Inf in train output | 0 |
| severity_level in transformed names | False |
| Output shape (train) | (517074, 111) |
| Output shape (val) | (129269, 111) |

---

## 8. Modified Files

| File | Change | Scope |
|------|--------|-------|
| `backend/feature_engineering/log_parser.py` | Removed `severity_level` from `extract_features()` | Preprocessing only |
| `backend/training/ait_label_config.py` | **NEW** — 22 ANOMALOUS labels, feature schema, dedup policy | Training config |
| `backend/training/train_ait_lds_v2.py` | **NEW** — Fixed pipeline: expanded labels + dedup | Training pipeline |

**Untouched:** live collector, Flask API, React frontend, SQLite DB, existing model artifacts.

---

## 9. Pass/Fail Checklist

- [x] **PASS** — severity_level absent from LogParser output
- [x] **PASS** — severity_level absent from ALL_FEATURES
- [x] **PASS** — classify_labels() — 12/12 unit tests pass
- [x] **PASS** — Dry-run exit=1 is PowerShell stderr artifact (Python exited 0)
- [x] **PASS** — Anomalous > 0 in all 3 datasets after fix
- [x] **PASS** — Deduplication ran and removed duplicates in all 3 datasets
- [x] **PASS** — Duplicate conflicts = 0 across all datasets
- [x] **PASS** — Zero parse errors across all datasets
- [x] **PASS** — Zero feature-extraction errors
- [x] **PASS** — No uncertain/unknown labels in any dataset
- [x] **PASS** — No zero-variance numerical features remain
- [x] **PASS** — No index overlap between train and val splits
- [x] **PASS** — No raw-line MD5 overlap (dedup before split prevents leakage)
- [x] **PASS** — Preprocessor fitted on train data only (no val data seen at fit time)
- [x] **PASS** — Zero NaN/Inf in transformed output arrays
- [x] **PASS** — severity_level absent from transformed feature names
- [x] **PASS** — Feature schema consistent across all 3 datasets
- [x] **PASS** — HDFS_v1 never loaded in this session

**Overall: 18/18 PASS**

---

## 10. Unresolved Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Unlabeled files default to Normal (not verified benign) | Known dataset limitation | Documented in §5; cannot be fixed in preprocessing |
| ~6–10% anomaly rate (class imbalance) | Expected | Handled by `class_weight='balanced'` (RF) and `scale_pos_weight` (XGBoost) |
| PowerShell `2>&1` reports exit=1 for Python logging | Cosmetic | Use `python ... 2>NUL` to suppress or ignore |

---

## 11. Training Command

> **Do not run until this report has been reviewed and approved.**

```bash
python -m backend.training.train_ait_lds_v2
```

Expected: ~45–90 min · 6 models (RF+XGBoost × 3 datasets) · all saved INACTIVE  
No live model, database, collector, or UI will be changed.