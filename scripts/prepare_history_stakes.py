"""Create minimal web data from the figure's workbook and November GNSS annex."""
import argparse
import json
import re
from pathlib import Path
import openpyxl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    project = parser.parse_args().project
    out = Path(__file__).resolve().parents[1] / 'data'
    workbook = project / 'Documentos/bm_hist/bm_hist.xlsx'
    rows = list(openpyxl.load_workbook(workbook, data_only=True)['Hoja1'].values)
    records = []
    for row in rows[1:]:
        year, period, _, balance, uncertainty, _, _, source = row
        if not isinstance(year, (int, float)) or not 2003 <= year <= 2024:
            continue
        records.append(dict(year=int(year), period=period, balance=balance, uncertainty=uncertainty,
                            sourceLabel=source, provenance='Documentos/bm_hist/bm_hist.xlsx · Hoja1'))
    assert len(records) == 22 and sum(r['balance'] is None for r in records) == 5
    for year, value in {2003:-.88, 2004:.36, 2009:.69, 2022:-2.67, 2024:.88}.items():
        assert next(r['balance'] for r in records if r['year'] == year) == value
    data = dict(unit='m eq.a.', figure=2, printedPage=5, records=records,
                source='Informe final — Mocho 2025–2026, Figura 2, p. 5; libro original bm_hist.xlsx, identificado en Codes/Figures_glaciares_chilenos.ipynb.',
                note='Los años sin balance anual son null; no equivalen a cero. Incertidumbres según columna incer, sin asignar un nivel de confianza no documentado.')
    (out / 'mass-balance-history.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    annex = project / '1_DASHBOARD/AnexosDigitales'
    path = next(annex.glob('3_*/3_GPS/Nov2025/Balizas_Mocho20251121.geojson'))
    original = json.loads(path.read_text(encoding='utf-8'))
    features = []
    for feature in original['features']:
        p = feature['properties']
        name = p['Name'].strip()
        if not re.fullmatch(r'B\d+[a-zA-Z]?', name):
            continue
        lon, lat = p['Longitude'], p['Latitude']
        assert -72.1 < lon < -71.9 and -40 < lat < -39.8
        date = p['Averaging start'][:10]
        assert date in ('2025-11-22', '2025-11-23')
        features.append(dict(type='Feature', id=name, geometry=dict(type='Point', coordinates=[lon, lat]),
                             properties=dict(name=name, date=date,
                                             source='Anexo 3 · GNSS, noviembre de 2025',
                                             awsSector=name == 'B15')))
    features.sort(key=lambda f: (int(re.search(r'\d+', f['id']).group()), f['id']))
    assert len(features) == len({f['id'] for f in features})
    collection = dict(type='FeatureCollection', features=features,
                      provenance=dict(path=path.relative_to(annex).as_posix(), outputCrs='EPSG:4326',
                                      coordinates='Campos Longitude/Latitude WGS84 del levantamiento; geometría original UTM 18S.',
                                      note='Fechas tomadas de Averaging start. Alturas elipsoidales excluidas; no son elevaciones sobre el nivel del mar.'))
    (out / 'stakes.geojson').write_text(json.dumps(collection, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(records)} hydrological years; {len(features)} stakes: ' + ', '.join(f['id'] for f in features))


if __name__ == '__main__':
    main()
