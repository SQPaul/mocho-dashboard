const $ = s => document.querySelector(s);
const ns = 'http://www.w3.org/2000/svg';
const number = n => n.toLocaleString('es-CL', {minimumFractionDigits:2, maximumFractionDigits:2});
const signed = n => `${n > 0 ? '+' : ''}${number(n)}`;
function svgNode(tag, attrs, text) {
  const el = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  return el;
}
async function initHistory() {
  const response = await fetch('./data/mass-balance-history.json');
  if (!response.ok) throw new Error('Datos no disponibles');
  const {records} = await response.json();
  const start = $('#history-start'), end = $('#history-end'), chart = $('#history-chart');
  for (const select of [start, end]) for (const row of records) select.add(new Option(row.period, row.year));
  start.value = records[0].year; end.value = records.at(-1).year;
  function inspect(row) {
    $('#history-year').textContent = row.period;
    $('#history-value').textContent = row.balance === null ? 'Sin dato' : `${signed(row.balance)} m eq.a.`;
    $('#history-detail').textContent = row.balance === null
      ? 'La Figura 2 no presenta un balance anual para este período. No equivale a un balance cero.'
      : `${row.balance > 0 ? 'Ganancia' : 'Pérdida'} de masa anual. ${row.uncertainty === null ? 'Incertidumbre no indicada en el libro original.' : `Incertidumbre: ± ${number(row.uncertainty)} m eq.a., según el libro original.`}`;
    for (const mark of chart.querySelectorAll('[data-year]')) mark.classList.toggle('selected', Number(mark.dataset.year) === row.year);
  }
  function render() {
    const rows = records.filter(r => r.year >= +start.value && r.year <= +end.value);
    const measured = rows.filter(r => r.balance !== null);
    $('#history-summary').textContent = `${measured.length} balances · ${measured.filter(r => r.balance > 0).length} positivos · ${rows.length - measured.length} sin dato`;
    chart.replaceChildren();
    const w = Math.max(720, rows.length * 39 + 80), h = 370, left = 54, right = w - 20;
    const y = value => 28 + (1.2 - value) / 4.4 * 258;
    const zero = y(0), step = (right - left) / rows.length;
    chart.setAttribute('viewBox', `0 0 ${w} ${h}`);
    chart.style.minWidth = `${Math.min(w, 820)}px`;
    chart.append(svgNode('title', {}, 'Balance de masa anual del glaciar Mocho'));
    for (const tick of [1, .5, 0, -.5, -1, -1.5, -2, -2.5, -3]) {
      chart.append(svgNode('line', {x1:left, x2:right, y1:y(tick), y2:y(tick), class:tick === 0 ? 'zero-line' : 'chart-grid'}));
      chart.append(svgNode('text', {x:left-12, y:y(tick)+4, 'text-anchor':'end', class:'chart-tick'}, tick.toLocaleString('es-CL')));
    }
    chart.append(svgNode('text', {x:left, y:14, class:'chart-unit'}, 'm eq.a.'));
    rows.forEach((row, i) => {
      const x = left + step * (i + .5), missing = row.balance === null;
      const group = svgNode('g', {tabindex:0, role:'button', 'data-year':row.year,
        'aria-label':`${row.period}: ${missing ? 'sin dato' : `${signed(row.balance)} metros equivalentes de agua`}`,
        class:`year-mark ${missing ? 'missing' : row.balance > 0 ? 'positive' : 'negative'}`});
      group.append(svgNode('rect', {x:x-step/2+1, y:25, width:step-2, height:270, class:'hit-area'}));
      if (missing) {
        group.append(svgNode('text', {x, y:zero+5, 'text-anchor':'middle', class:'missing-mark'}, '×'));
      } else {
        group.append(svgNode('rect', {x:x-step*.28, y:Math.min(zero, y(row.balance)), width:step*.56,
          height:Math.max(1, Math.abs(y(row.balance)-zero)), rx:2, class:'balance-bar'}));
        if ($('#history-uncertainty').checked && row.uncertainty !== null) {
          const upper = y(row.balance+row.uncertainty), lower = y(row.balance-row.uncertainty);
          group.append(svgNode('path', {d:`M ${x} ${upper} V ${lower} M ${x-4} ${upper} H ${x+4} M ${x-4} ${lower} H ${x+4}`, class:'uncertainty-line'}));
        }
      }
      group.append(svgNode('text', {transform:`translate(${x+3} 307) rotate(-55)`, 'text-anchor':'end', class:'chart-tick'}, row.period));
      group.addEventListener('pointerenter', () => inspect(row));
      group.addEventListener('click', () => inspect(row));
      group.addEventListener('focus', () => inspect(row));
      group.addEventListener('keydown', e => {
        if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) {
          e.preventDefault();
          const marks = [...chart.querySelectorAll('[data-year]')];
          const target = e.key === 'Home' ? 0 : e.key === 'End' ? rows.length-1 : Math.max(0, Math.min(rows.length-1, i+(e.key === 'ArrowRight' ? 1 : -1)));
          marks[target].focus();
        } else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inspect(row); }
      });
      chart.append(group);
    });
    const body = $('#history-table tbody'); body.replaceChildren();
    for (const row of rows) {
      const tr = document.createElement('tr');
      for (const value of [row.period, row.balance === null ? 'Sin dato' : signed(row.balance), row.uncertainty === null ? 'No indicada' : `± ${number(row.uncertainty)}`]) {
        const td = document.createElement('td'); td.textContent = value; tr.append(td);
      }
      body.append(tr);
    }
    inspect(rows.at(-1));
  }
  start.onchange = () => {if (+start.value > +end.value) end.value = start.value; render();};
  end.onchange = () => {if (+end.value < +start.value) start.value = end.value; render();};
  $('#history-uncertainty').onchange = render;
  $('#history-reset').onclick = () => {start.value=records[0].year; end.value=records.at(-1).year; $('#history-uncertainty').checked=false; render();};
  $('#history-download').onclick = () => {
    const rows = records.filter(r => r.year >= +start.value && r.year <= +end.value);
    const csv = 'periodo,balance_m_eq_a,incertidumbre_m_eq_a,fuente\r\n' + rows.map(r => `${r.period},${r.balance ?? ''},${r.uncertainty ?? ''},"Informe Mocho 2025-2026; Figura 2 p.5; bm_hist.xlsx"`).join('\r\n');
    const url = URL.createObjectURL(new Blob(['\uFEFF'+csv], {type:'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href=url; a.download=`mocho-balance-${start.value}-${+end.value+1}.csv`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  render(); $('#history-loading').hidden = true; $('#history-content').hidden = false;
}
initHistory().catch(() => {$('#history-loading').textContent='No fue posible cargar la serie histórica. Recarga la página para reintentar.';});
