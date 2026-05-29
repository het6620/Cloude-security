// Update nav progress pill on every page
async function loadNavProgress() {
  try {
    const r = await fetch('/api/progress');
    const d = await r.json();
    const el = document.getElementById('nav-pct');
    if (el) el.textContent = d.percent + '%';
  } catch {}
}
loadNavProgress();

async function resetProgress() {
  if (!confirm('Reset all your learning progress and quiz results?')) return;
  await fetch('/api/reset', { method: 'POST' });
  location.reload();
}
