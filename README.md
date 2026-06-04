# 🏗️ STAAD Structural Analysis Tool

> A Django web application for structural engineers to analyze STAAD.Pro output files — node displacement compliance checking and member section optimization in one tool.

---

## 📌 About

The **STAAD Structural Analysis Tool** accepts two types of STAAD.Pro export files and delivers instant structural analysis results through a clean browser-based dashboard — no manual calculations, no scripting required.

- Upload an **Excel file** → get IS Code node displacement analysis
- Upload a **CSV file** → get rule-based member section optimization

---

## ✨ Features

- **Dual-format input** — Excel (.xlsx/.xls) for node displacements, CSV for member forces
- **IS Code compliance** — classifies every node as Safe / Warning / Critical based on resultant displacement thresholds
- **Member optimizer** — computes recommended area, depth, width, Ix, Iz, weight, and scale factor for Beams, Columns, and Braces
- **KPI dashboard** — 5 summary cards (Total, Critical/Over, Warning/Under, Safe, Max/Avg)
- **Search & filter** — live client-side search + dropdown filters by load case, member type, and utilization status
- **CSV export** — one-click download of full results including all predicted section targets
- **Session-based** — no login or database setup required for basic use
- **Responsive UI** — Bootstrap 5 + custom CSS design tokens, works on desktop and tablet

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 6.0 |
| Processing | pandas, openpyxl, xlrd |
| Frontend | Django Templates, Bootstrap 5, Vanilla JS |
| Database | SQLite (via Django ORM) |
| Server | Django Dev Server (WSGI) |

---

## 📂 Project Structure

```
civilproject/
├── manage.py                        # Django entry point
├── db.sqlite3                       # SQLite database
├── predictor.py                     # Core engine — displacement parser + member optimizer
├── MODEL 1 (1).xlsx                 # Sample STAAD.Pro Excel file for testing
├── test_project.py                  # Test script
├── civilproject/
│   ├── settings.py                  # Django configuration
│   ├── urls.py                      # Root URL routing
│   └── wsgi.py                      # WSGI entry point
└── civilapp/
    ├── views.py                     # index, upload_file, export_csv
    ├── urls.py                      # App URL patterns
    ├── models.py                    # UploadSession, MemberResult
    ├── admin.py                     # Admin registrations
    └── templates/
        ├── base.html                # Shared layout + nav
        ├── upload.html              # Upload page
        ├── results_displacement.html # Node displacement dashboard
        └── results_members.html     # Member optimization dashboard
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/civilproject.git
cd civilproject
```

### 2. Install dependencies

```bash
pip install django pandas openpyxl xlrd
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Run the server

```bash
python manage.py runserver
```

### 5. Open in browser

```
http://127.0.0.1:8000/
```

---

## 📁 Input File Formats

### Excel — Node Displacement (STAAD.Pro Export)

| Column | Content |
|---|---|
| B | Node number |
| C | Load case string (e.g. `1 DL`, `2 LL`) |
| D–F | X, Y, Z displacements (mm) |
| G | Resultant displacement (mm) |
| H–J | Rotations rX, rY, rZ (radians) — optional |

### CSV — Member Forces (Minimum Required Columns)

| Column | Type | Description |
|---|---|---|
| `member_type` | string | BEAM / COLUMN / BRACE |
| `span_m` | float | Member span (metres) |
| `axial_kN` | float | Axial force (kN) |
| `moment_x_kNm` | float | Bending moment X (kN·m) |
| `moment_z_kNm` | float | Bending moment Z (kN·m) |
| `shear_y_kN` | float | Shear force Y (kN) |
| `utilization` | float | Utilization ratio (e.g. 0.85) |

---

## 📊 Output — What You Get

### Node Displacement Results
- Per-node status: **Safe** (≤1.0 mm) / **Warning** (1.0–2.0 mm) / **Critical** (>2.0 mm)
- Maximum resultant node + load case
- Top-5 critical nodes
- Full table filterable by load case

### Member Optimization Results

| Output Field | Unit | Description |
|---|---|---|
| `target_area_cm2` | cm² | Recommended cross-sectional area |
| `target_depth_mm` | mm | Recommended section depth |
| `target_width_mm` | mm | Recommended section width |
| `target_Ix_cm4` | cm⁴ | Moment of inertia — strong axis |
| `target_Iz_cm4` | cm⁴ | Moment of inertia — weak axis |
| `target_weight_kgm` | kg/m | Self-weight per unit length |
| `scale_factor` | ratio | Resize factor vs current section |

---

## 🌐 URL Routes

| Method | URL | Description |
|---|---|---|
| GET | `/` | Upload page |
| POST | `/upload/` | Process file, render results |
| GET | `/export/` | Download results as CSV |
| GET/POST | `/admin/` | Django admin panel |

---

## ⚠️ IS Code Thresholds

```
Resultant Displacement > 2.0 mm  →  🔴 Critical
Resultant Displacement 1.0–2.0 mm →  🟡 Warning
Resultant Displacement ≤ 1.0 mm  →  🟢 Safe
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the MIT License.

---

*Built for Civil & Structural Engineering workflows | Django 6.0 | May 2026*
