"""
STAAD Structural Optimizer — Unified Predictor
-----------------------------------------------
Handles TWO data formats:
  1. Excel (.xlsx/.xls) — STAAD.Pro Node Displacement output
  2. CSV               — Member force data (BEAM/COLUMN/BRACE)
"""

import math
import pandas as pd

# ─── IS Code Thresholds ───────────────────────────────────────────
THRESHOLD_CRITICAL = 2.0   # mm — resultant > 2.0 → Critical
THRESHOLD_WARNING  = 1.0   # mm — resultant 1.0–2.0 → Warning

LC_LABELS = {
    '1 DL': 'DL',
    '2 LL': 'LL',
    '3 GENERATED INDIAN CODE GENRAL_STRUCTURES 1': 'IS Combo 1',
    '4 GENERATED INDIAN CODE GENRAL_STRUCTURES 2': 'IS Combo 2',
    '5 GENERATED INDIAN CODE GENRAL_STRUCTURES 3': 'IS Combo 3',
    '6 GENERATED INDIAN CODE GENRAL_STRUCTURES 4': 'IS Combo 4',
}

# ═══════════════════════════════════════════════════════════════════
# FORMAT 1 — EXCEL: Node Displacement Parser
# ═══════════════════════════════════════════════════════════════════

def get_disp_status(resultant_mm):
    r = abs(float(resultant_mm))
    if r > THRESHOLD_CRITICAL:
        return 'critical'
    elif r > THRESHOLD_WARNING:
        return 'warning'
    return 'safe'


def parse_excel_displacement(filepath_or_buffer):
    df_raw = pd.read_excel(filepath_or_buffer, sheet_name=0, header=None)
    records = []
    current_node = None

    for _, row in df_raw.iterrows():
        try:
            n = int(row[1])
            current_node = n
        except Exception:
            pass

        if current_node and isinstance(row[2], str):
            lc_clean = row[2].strip()
            if lc_clean in ('L/C', '', 'Node') or not lc_clean:
                continue
            try:
                records.append({
                    'node':            current_node,
                    'load_case':       lc_clean,
                    'load_case_short': LC_LABELS.get(lc_clean, lc_clean),
                    'X_mm':            round(float(row[3]), 3),
                    'Y_mm':            round(float(row[4]), 3),
                    'Z_mm':            round(float(row[5]), 3),
                    'Resultant_mm':    round(float(row[6]), 3),
                    'rX_rad':          round(float(row[7]) if str(row[7]) not in ('nan','') else 0, 4),
                    'rY_rad':          round(float(row[8]) if str(row[8]) not in ('nan','') else 0, 4),
                    'rZ_rad':          round(float(row[9]) if str(row[9]) not in ('nan','') else 0, 4),
                })
            except Exception:
                continue

    df = pd.DataFrame(records)
    if not df.empty:
        df['status'] = df['Resultant_mm'].apply(get_disp_status)
    return df


def compute_displacement_summary(df):
    total_nodes    = df['node'].nunique()
    node_max       = df.groupby('node')['Resultant_mm'].max()
    node_status    = node_max.apply(get_disp_status)
    critical_nodes = int((node_status == 'critical').sum())
    warning_nodes  = int((node_status == 'warning').sum())
    safe_nodes     = int((node_status == 'safe').sum())
    max_idx        = df['Resultant_mm'].idxmax()
    max_resultant  = round(float(df.loc[max_idx, 'Resultant_mm']), 3)
    max_node       = int(df.loc[max_idx, 'node'])
    max_lc         = df.loc[max_idx, 'load_case_short']
    avg_resultant  = round(float(df['Resultant_mm'].mean()), 3)
    top5 = (
        node_max.sort_values(ascending=False).head(5)
        .reset_index().rename(columns={'Resultant_mm': 'max_resultant'})
        .to_dict('records')
    )
    return {
        'total_nodes': total_nodes,
        'critical_nodes': critical_nodes,
        'warning_nodes': warning_nodes,
        'safe_nodes': safe_nodes,
        'max_resultant': max_resultant,
        'max_resultant_node': max_node,
        'max_resultant_lc': max_lc,
        'avg_resultant': avg_resultant,
        'max_Y_mm': round(float(df['Y_mm'].abs().max()), 3),
        'top5_critical': top5,
        'threshold_critical': THRESHOLD_CRITICAL,
        'threshold_warning': THRESHOLD_WARNING,
    }


def get_load_cases(df):
    return sorted(df['load_case_short'].unique().tolist())


# ═══════════════════════════════════════════════════════════════════
# FORMAT 2 — CSV: Member Force Optimizer
# ═══════════════════════════════════════════════════════════════════

def get_member_status(utilization):
    u = float(utilization)
    if u > 1.0:
        return 'over'
    elif u < 0.5:
        return 'under'
    return 'safe'


def _predict_member(row):
    """Rule-based structural section optimization per member row."""
    axial   = float(row.get('axial_kN', 0))
    mx      = float(row.get('moment_x_kNm', 0))
    mz      = float(row.get('moment_z_kNm', 0))
    shear   = float(row.get('shear_y_kN', 0))
    span    = float(row.get('span_m', 1))
    util    = float(row.get('utilization', 0.85))
    area    = float(row.get('current_area_cm2', 50))
    mtype   = str(row.get('member_type', 'beam')).lower()

    # Target area based on utilization scaling to 0.85
    target_area = area * (util / 0.85)
    type_factor = {'beam': 1.0, 'column': 1.15, 'brace': 0.90}.get(mtype, 1.0)
    target_area = max(target_area * type_factor, 10.0)

    # Dimensions: depth = 1.5 × width; for beams add span correction
    area_mm2  = target_area * 100
    width_mm  = math.sqrt(area_mm2 / 1.5)
    depth_mm  = 1.5 * width_mm
    if mtype == 'beam':
        depth_mm *= max(1.0, span / 3.0) * 0.6
        width_mm  = depth_mm / 1.5

    depth_mm = round(depth_mm, 1)
    width_mm = round(width_mm, 1)

    Ix_cm4 = round((width_mm * depth_mm**3) / 12 / 10000, 1)
    Iz_cm4 = round((depth_mm * width_mm**3) / 12 / 10000, 1)
    weight  = round(target_area * 7850 / 10000, 1)
    scale   = round(target_area / max(area, 1), 2)

    return {
        'target_area_cm2':   round(target_area, 1),
        'target_depth_mm':   depth_mm,
        'target_width_mm':   width_mm,
        'target_Ix_cm4':     Ix_cm4,
        'target_Iz_cm4':     Iz_cm4,
        'target_weight_kgm': weight,
        'scale_factor':      scale,
    }


def process_member_csv(df):
    """
    Process member CSV dataframe and return list of result dicts.
    Expects columns: model, member_id, member_type, span_m, stories,
                     axial_kN, moment_x_kNm, moment_z_kNm, shear_y_kN,
                     deflection_mm, utilization, section_name, current_area_cm2
    """
    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    results = []
    for _, row in df.iterrows():
        rd = row.to_dict()
        rd.setdefault('section_name',     'N/A')
        rd.setdefault('current_area_cm2', 50.0)
        rd.setdefault('deflection_mm',    0.0)
        rd.setdefault('stories',          1)
        rd.setdefault('model',            'MODEL 1')
        rd.setdefault('member_id',        str(_ + 1))

        pred = _predict_member(rd)
        rd.update(pred)

        # Round display values
        for f in ['span_m','axial_kN','moment_x_kNm','moment_z_kNm',
                  'shear_y_kN','deflection_mm','utilization','current_area_cm2']:
            try:
                rd[f] = round(float(rd[f]), 2)
            except Exception:
                pass

        rd['status'] = get_member_status(rd['utilization'])
        results.append(rd)

    return results


def compute_member_summary(results):
    total       = len(results)
    over_util   = sum(1 for r in results if r['status'] == 'over')
    under_util  = sum(1 for r in results if r['status'] == 'under')
    safe_count  = sum(1 for r in results if r['status'] == 'safe')
    avg_scale   = round(sum(float(r.get('scale_factor', 1)) for r in results) / total, 2) if total else 1.0

    # Per model counts
    models = {}
    for r in results:
        m = r.get('model', 'MODEL 1')
        models[m] = models.get(m, 0) + 1

    # Most critical member
    crit = max(results, key=lambda r: float(r.get('utilization', 0)))

    return {
        'total_members':  total,
        'over_utilized':  over_util,
        'under_utilized': under_util,
        'safe_count':     safe_count,
        'avg_scale':      avg_scale,
        'model_counts':   models,
        'critical_member': {
            'model':      crit.get('model', ''),
            'member_id':  crit.get('member_id', ''),
            'member_type':crit.get('member_type', ''),
            'utilization':crit.get('utilization', 0),
        },
    }