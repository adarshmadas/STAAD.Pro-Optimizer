import sys, os, io
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictor import (
    # Excel node displacement
    parse_excel_displacement,
    compute_displacement_summary,
    get_load_cases,
    # CSV member optimizer
    process_member_csv,
    compute_member_summary,
)


def index(request):
    return render(request, 'upload.html')


def upload_file(request):
    if request.method != 'POST':
        return redirect('index')

    uploaded = request.FILES.get('data_file')
    if not uploaded:
        return render(request, 'upload.html', {'error': 'Please select a file to upload.'})

    name = uploaded.name.lower()
    if not (name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv')):
        return render(request, 'upload.html',
                      {'error': 'Only .xlsx, .xls, or .csv files are accepted.'})

    try:
        file_bytes = uploaded.read()
        buf = io.BytesIO(file_bytes)

        # ── FORMAT 1: Excel → Node Displacement ──────────────────
        if name.endswith('.xlsx') or name.endswith('.xls'):
            buf.seek(0)
            df = parse_excel_displacement(buf)
            if df.empty:
                return render(request, 'upload.html',
                              {'error': 'No displacement data found in Excel file.'})

            summary  = compute_displacement_summary(df)
            lc_list  = get_load_cases(df)
            results  = df.to_dict('records')

            request.session['results']       = results
            request.session['file_name']     = uploaded.name
            request.session['data_format']   = 'displacement'

            return render(request, 'results_displacement.html', {
                'results':   results,
                'summary':   summary,
                'lc_list':   lc_list,
                'file_name': uploaded.name,
            })

        # ── FORMAT 2: CSV → Member Optimizer ─────────────────────
        else:
            buf.seek(0)
            df_raw = pd.read_csv(buf)
            if df_raw.empty:
                return render(request, 'upload.html',
                              {'error': 'Uploaded CSV is empty.'})

            # Validate required columns
            required = {'member_type', 'span_m', 'axial_kN',
                        'moment_x_kNm', 'moment_z_kNm', 'shear_y_kN', 'utilization'}
            missing = required - set(df_raw.columns)
            if missing:
                return render(request, 'upload.html',
                              {'error': f'Missing columns in CSV: {", ".join(sorted(missing))}'})

            results = process_member_csv(df_raw)
            summary = compute_member_summary(results)

            request.session['results']     = results
            request.session['file_name']   = uploaded.name
            request.session['data_format'] = 'member'

            # Get unique models and member types for filters
            models   = sorted(set(r.get('model', '') for r in results))
            mtypes   = sorted(set(str(r.get('member_type', '')).upper() for r in results))

            return render(request, 'results_members.html', {
                'results':   results,
                'summary':   summary,
                'models':    models,
                'mtypes':    mtypes,
                'file_name': uploaded.name,
            })

    except Exception as e:
        return render(request, 'upload.html',
                      {'error': f'Error processing file: {str(e)}'})


def export_csv(request):
    results = request.session.get('results', [])
    if not results:
        return redirect('index')
    df = pd.DataFrame(results)
    fmt = request.session.get('data_format', 'results')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{fmt}_results.csv"'
    df.to_csv(response, index=False)
    return response