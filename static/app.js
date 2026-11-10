let courseChart, distributionChart, questionChart, responseChart;
const palette = ['#6b49e7','#4c83f2','#20b886','#f3a449','#e56b91'];
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const fmt = (n) => Number(n || 0).toFixed(2);

function navTo(view) {
  $$('.view').forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
  $$('.nav-link').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  const titles = {dashboard:'Dashboard', feedback:'Give Feedback', analytics:'Analytics & Reports'};
  $('#page-title').textContent = titles[view] || 'Dashboard';
  if (view === 'analytics') refreshDashboard();
  window.scrollTo({top:0, behavior:'smooth'});
}
$$('.nav-link').forEach(b => b.addEventListener('click', () => navTo(b.dataset.view)));
$$('[data-go]').forEach(b => b.addEventListener('click', () => navTo(b.dataset.go)));

const commonOptions = {
  responsive:true, maintainAspectRatio:false, animation:{duration:850,easing:'easeOutQuart'},
  plugins:{legend:{display:false},tooltip:{backgroundColor:'#201e4e',padding:11,cornerRadius:8,titleFont:{family:'DM Sans'},bodyFont:{family:'DM Sans'}}}
};
function makeCharts() {
  const courseCtx = $('#courseChart');
  courseChart = new Chart(courseCtx, {type:'bar', data:{labels:[],datasets:[{data:[],backgroundColor:palette,borderRadius:7,borderSkipped:false,maxBarThickness:35}]},
    options:{...commonOptions,scales:{x:{grid:{display:false},ticks:{color:'#7d819f',font:{family:'DM Sans',size:10}}},y:{min:0,max:5,ticks:{stepSize:1,color:'#9b9db1',font:{size:10}},grid:{color:'#f0f0f7'}}}}});
  distributionChart = new Chart($('#distributionChart'), {type:'doughnut',data:{labels:['5 Excellent','4 Good','3 Fair','2 Low','1 Poor'],datasets:[{data:[0,0,0,0,0],backgroundColor:palette,borderWidth:0,hoverOffset:7}]},
    options:{...commonOptions,cutout:'72%',plugins:{...commonOptions.plugins,legend:{display:false}}}});
  questionChart = new Chart($('#questionChart'), {type:'bar',data:{labels:[],datasets:[{data:[],backgroundColor:'#8065ed',borderRadius:6,borderSkipped:false,maxBarThickness:38}]},
    options:{...commonOptions,indexAxis:'y',scales:{x:{min:0,max:5,ticks:{stepSize:1,color:'#9b9db1'},grid:{color:'#f0f0f7'}},y:{grid:{display:false},ticks:{color:'#6f7491',font:{size:10}}}}}});
  responseChart = new Chart($('#responseChart'), {type:'bar',data:{labels:[],datasets:[{data:[],backgroundColor:'#4c83f2',borderRadius:6,borderSkipped:false,maxBarThickness:38}]},
    options:{...commonOptions,scales:{x:{grid:{display:false},ticks:{color:'#7d819f'}},y:{beginAtZero:true,ticks:{precision:0,color:'#9b9db1'},grid:{color:'#f0f0f7'}}}}});
}
function updateChart(chart, labels, values, label) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = values;
  if (label) chart.data.datasets[0].label = label;
  chart.update();
}
function renderCourses(courses) {
  const list = $('#course-list');
  list.innerHTML = courses.map(c => {
    const hidden = c.suppressed;
    const score = hidden ? '—' : fmt(c.average);
    const width = hidden ? 0 : Math.max(0, Math.min(100, (c.average || 0) * 20));
    return `<div class="course-row"><div class="course-code">${c.code}</div><div class="course-name" title="${c.name}">${c.name}</div><div class="progress-track"><div class="progress-fill" style="width:${width}%"></div></div><div class="course-score">${score}<small> / 5</small></div></div>`;
  }).join('');
}
function renderReport(courses) {
  $('#report-table').innerHTML = courses.map(c => {
    const hidden = c.suppressed;
    return `<tr><td><b>${c.code}</b> <span style="color:#8d91a8">· ${c.name}</span></td><td>${c.responses}</td><td>${hidden ? 'Suppressed' : fmt(c.average)}</td><td><span class="status-pill ${hidden ? 'muted' : ''}">${hidden ? 'Privacy protected' : (c.responses ? 'Available' : 'Awaiting feedback')}</span></td></tr>`;
  }).join('');
}
function renderAnalytics(data) {
  const courseFilter = $('#analytics-course')?.value || 'ALL';
  const selected = data.courses.filter(c => courseFilter === 'ALL' || c.code === courseFilter);
  const visible = selected.filter(c => !c.suppressed && c.responses > 0);
  let qValues = [0,0,0,0,0];
  if (visible.length) qValues = qValues.map((_, i) => {
    const vals = visible.map(c => c.question_averages[i]).filter(v => v !== null && v !== undefined);
    return vals.length ? +(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(2) : 0;
  });
  updateChart(questionChart, window.QUESTIONS.map((_,i)=>`Q${i+1}`), qValues);
  updateChart(responseChart, data.courses.map(c=>c.code), data.courses.map(c=>c.responses));
  renderReport(data.courses);
}
async function refreshDashboard() {
  try {
    const res = await fetch('/api/summary');
    const data = await res.json();
    $('#total-responses').textContent = data.total_responses.toLocaleString();
    $('#overall-average').textContent = fmt(data.overall_average);
    $('#total-ratings').textContent = data.total_ratings.toLocaleString();
    const courses = data.courses;
    updateChart(courseChart, courses.map(c=>c.code), courses.map(c=>c.suppressed ? 0 : (c.average || 0)));
    const dist = data.distribution;
    updateChart(distributionChart, ['5 Excellent','4 Good','3 Fair','2 Low','1 Poor'], [dist['5'],dist['4'],dist['3'],dist['2'],dist['1']]);
    renderCourses(courses);
    renderAnalytics(data);
  } catch (e) { showToast('Could not load analytics. Check that the server is running.'); }
}
$('#analytics-course').addEventListener('change', async () => {
  const data = await (await fetch('/api/summary')).json();
  renderAnalytics(data);
});
$('#comment').addEventListener('input', e => $('#char-count').textContent = `${e.target.value.length} / 500`);
$$('.rating-option input').forEach(input => input.addEventListener('change', e => {
  e.target.closest('.question-card').classList.add('answered');
}));
function showToast(message) {
  const toast = $('#toast'); toast.textContent = message; toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3200);
}
$('#feedback-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const course_code = $('#course-select').value;
  const ratings = window.QUESTIONS.map((_,i) => {
    const selected = $(`input[name="q${i}"]:checked`);
    return selected ? Number(selected.value) : null;
  });
  const message = $('#form-message');
  if (!course_code) { message.className='form-message error'; message.textContent='Please select a course.'; return; }
  if (ratings.some(r => r === null)) { message.className='form-message error'; message.textContent='Please rate all five questions before submitting.'; return; }
  const button = $('#submit-btn'); button.disabled = true; button.textContent = 'Submitting…';
  try {
    const response = await fetch('/api/feedback', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({course_code,ratings,comment:$('#comment').value})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Submission failed.');
    message.className='form-message success'; message.textContent=result.message;
    showToast('Feedback saved · charts updated');
    $('#feedback-form').reset(); $('#char-count').textContent='0 / 500'; $$('.question-card').forEach(q=>q.classList.remove('answered'));
    await refreshDashboard();
    setTimeout(()=>navTo('dashboard'),650);
  } catch (err) { message.className='form-message error'; message.textContent=err.message; }
  finally { button.disabled=false; button.innerHTML='Submit feedback <span>→</span>'; }
});
makeCharts();
refreshDashboard();
