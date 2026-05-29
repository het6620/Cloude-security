const TOPIC_ICONS = {
  "what-is-cloud":"☁","cloud-history":"📅","cloud-models":"📐","cloud-types":"🏗",
  "cloud-providers":"🏢","cloud-security":"🛡","cloud-security-principles":"📋",
  "cloud-security-threats":"⚠️","cloud-security-tools":"🔧","cloud-security-compliance":"📜",
  "cloud-networking":"🌐","cloud-storage":"💾","cloud-devops":"⚙️","cloud-career":"🎯"
};
const TOPIC_DESC = {
  "what-is-cloud":"Foundations of cloud computing","cloud-history":"Evolution of cloud tech",
  "cloud-models":"IaaS, PaaS, SaaS explained","cloud-types":"Public, private, hybrid",
  "cloud-providers":"AWS, Azure, GCP & more","cloud-security":"Security fundamentals",
  "cloud-security-principles":"Core security principles","cloud-security-threats":"Common attack vectors",
  "cloud-security-tools":"Essential security tools","cloud-security-compliance":"GDPR, SOC2, HIPAA & more",
  "cloud-networking":"VPC, DNS, load balancing","cloud-storage":"Storage types & security",
  "cloud-devops":"CI/CD, IaC, containers","cloud-career":"Your path to the top"
};

async function loadDashboard() {
  const [topicsRes, progressRes] = await Promise.all([
    fetch('/api/topics'), fetch('/api/progress')
  ]);
  const topics = await topicsRes.json();
  const progress = await progressRes.json();
  const progressMap = {};
  progress.details.forEach(d => { progressMap[d.topic_slug] = d; });

  // Ring
  const pct = progress.percent;
  const circumference = 2 * Math.PI * 50;
  const offset = circumference - (pct / 100) * circumference;
  const ring = document.getElementById('ring-fill');
  if (ring) { ring.style.strokeDashoffset = offset; }
  const ringPct = document.getElementById('ring-pct');
  if (ringPct) ringPct.textContent = pct + '%';
  const dashComp = document.getElementById('dash-completed');
  if (dashComp) dashComp.textContent = progress.completed;
  const dashTotal = document.getElementById('dash-total');
  if (dashTotal) dashTotal.textContent = progress.total;

  // Topic progress list
  const list = document.getElementById('topic-progress-list');
  if (list) {
    list.innerHTML = topics.map(t => {
      const p = progressMap[t.slug];
      const score = p ? p.score : 0;
      const done = p && p.completed;
      return `<div class="tpl-item" onclick="location.href='/topic/${t.slug}'">
        <span class="tpl-status">${done ? '✅' : '⭕'}</span>
        <span class="tpl-name">${t.title}</span>
        <span class="tpl-score">${score}%</span>
        <div class="tpl-bar-wrap"><div class="tpl-bar" style="width:${score}%"></div></div>
      </div>`;
    }).join('');
  }

  // Roadmap
  const grid = document.getElementById('roadmap-grid');
  if (grid) {
    grid.innerHTML = topics.map((t,i) => {
      const p = progressMap[t.slug];
      const done = p && p.completed;
      return `<div class="roadmap-card ${done?'completed':''}" onclick="location.href='/topic/${t.slug}'">
        <div class="rc-badge ${done?'done':''}">${done?'✓ Done':'Start →'}</div>
        <div class="rc-icon">${TOPIC_ICONS[t.slug]||'📚'}</div>
        <div class="rc-title">${t.title}</div>
        <div class="rc-meta">${TOPIC_DESC[t.slug]||''}</div>
      </div>`;
    }).join('');
  }
}

loadDashboard();
