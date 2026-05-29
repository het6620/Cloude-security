// Sidebar nav
async function loadSidebar() {
  const [topicsRes, progressRes] = await Promise.all([
    fetch('/api/topics'), fetch('/api/progress')
  ]);
  const topics = await topicsRes.json();
  const progress = await progressRes.json();
  const progressMap = {};
  progress.details.forEach(d => { progressMap[d.topic_slug] = d; });

  const nav = document.getElementById('sidebar-nav');
  const parentTopics = topics.filter(t => !t.parent_slug);
  const childTopics = topics.filter(t => t.parent_slug);

  let html = '';
  parentTopics.forEach(t => {
    const p = progressMap[t.slug];
    const done = p && p.completed;
    html += `<div class="sb-item ${done?'completed':''} ${t.slug===CURRENT_SLUG?'active':''}"
      onclick="location.href='/topic/${t.slug}'">
      <span class="sb-check">${done?'✅':'⚪'}</span>
      <span>${t.title}</span>
    </div>`;
    const children = childTopics.filter(c => c.parent_slug === t.slug);
    children.forEach(c => {
      const cp = progressMap[c.slug];
      const cdone = cp && cp.completed;
      html += `<div class="sb-item sb-sub ${cdone?'completed':''} ${c.slug===CURRENT_SLUG?'active':''}"
        onclick="location.href='/topic/${c.slug}'">
        <span class="sb-check">${cdone?'✅':'⚪'}</span>
        <span>${c.title}</span>
      </div>`;
    });
  });
  nav.innerHTML = html;
}

// Render topic content
function renderContent() {
  const data = TOPIC_CONTENT[CURRENT_SLUG];
  if (!data) return;

  // Header
  document.getElementById('topic-header').innerHTML = `
    <div class="topic-icon-big">${data.icon}</div>
    <h1>${data.title}</h1>
    <div class="topic-intro">${data.intro}</div>
  `;
  document.title = data.title + ' — CloudHero';

  // Sections
  const contentEl = document.getElementById('topic-content');
  contentEl.innerHTML = data.sections.map(s => `
    <section class="content-section">
      <h3>${s.heading}</h3>
      <div class="body">${s.body}</div>
    </section>
  `).join('');
}

// ─── QUIZ ENGINE ───
let quizData = [];
let answeredMap = {};  // question_id -> was_correct

async function loadQuiz() {
  const [qRes, pRes] = await Promise.all([
    fetch(`/api/quiz/${CURRENT_SLUG}`),
    fetch(`/api/quiz/${CURRENT_SLUG}/progress`)
  ]);
  quizData = await qRes.json();
  const pData = await pRes.json();
  answeredMap = pData.answered || {};

  if (quizData.length === 0) return;

  const section = document.getElementById('quiz-section');
  section.style.display = 'block';

  updateScoreDisplay();
  renderQuizQuestions();
}

function updateScoreDisplay() {
  const total = quizData.length;
  const correct = Object.values(answeredMap).filter(v => v === 1).length;
  const el = document.getElementById('quiz-score-display');
  if (el) el.textContent = `✅ ${correct} / ${total} correct`;
}

function renderQuizQuestions() {
  const container = document.getElementById('quiz-questions');
  const letters = ['A','B','C','D'];

  container.innerHTML = quizData.map(q => {
    const alreadyCorrect = answeredMap[q.id] === 1;
    return `
    <div class="quiz-q-card" id="qcard-${q.id}">
      <div class="quiz-q-num">Question ${q.id}</div>
      <div class="quiz-q-text">${q.q}</div>
      <div class="quiz-options">
        ${q.options.map((opt, i) => `
          <div class="quiz-opt ${alreadyCorrect?'disabled':''}" data-qid="${q.id}" data-idx="${i}" onclick="selectOption(this, ${q.id}, ${i})">
            <span class="opt-letter">${letters[i]}</span>
            <span>${opt}</span>
          </div>
        `).join('')}
      </div>
      <button class="quiz-submit-btn" id="submit-${q.id}" onclick="submitAnswer(${q.id})">Submit Answer</button>
      <div class="quiz-msg" id="msg-${q.id}"></div>
    </div>`;
  }).join('');

  // Mark already-correct ones visually
  quizData.forEach(q => {
    if (answeredMap[q.id] === 1) {
      const card = document.getElementById('qcard-' + q.id);
      if (card) {
        const msg = document.getElementById('msg-' + q.id);
        msg.textContent = '✅ Already answered correctly!';
        msg.className = 'quiz-msg correct';
        msg.style.display = 'block';
      }
    }
  });
}

let selectedOptions = {};

function selectOption(el, qid, idx) {
  if (answeredMap[qid] === 1) return;
  // Deselect all
  document.querySelectorAll(`.quiz-opt[data-qid="${qid}"]`).forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  selectedOptions[qid] = idx;
  document.getElementById('submit-' + qid).style.display = 'inline-block';
}

async function submitAnswer(qid) {
  const selected = selectedOptions[qid];
  if (selected === undefined) return;

  const res = await fetch(`/api/quiz/${CURRENT_SLUG}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: qid, selected })
  });
  const data = await res.json();

  // Visual feedback
  const opts = document.querySelectorAll(`.quiz-opt[data-qid="${qid}"]`);
  opts.forEach((o, i) => {
    o.classList.add('disabled');
    if (i === data.correct_index) o.classList.add('correct');
    else if (i === selected && !data.correct) o.classList.add('wrong');
  });

  const submitBtn = document.getElementById('submit-' + qid);
  submitBtn.style.display = 'none';

  const msgEl = document.getElementById('msg-' + qid);
  msgEl.textContent = data.message;
  msgEl.className = 'quiz-msg ' + (data.correct ? 'correct' : 'wrong');
  msgEl.style.display = 'block';

  if (data.correct) {
    answeredMap[qid] = 1;
  }
  updateScoreDisplay();
  checkAllAnswered();
  loadNavProgress();
}

function checkAllAnswered() {
  const total = quizData.length;
  const correct = Object.values(answeredMap).filter(v => v === 1).length;
  const banner = document.getElementById('quiz-result-banner');
  if (correct === total) {
    banner.textContent = `🏆 Outstanding! You got all ${total} questions correct! Topic mastered!`;
    banner.className = 'quiz-result-banner pass';
    banner.style.display = 'block';
  } else if (Object.keys(answeredMap).length >= total) {
    banner.textContent = `📚 You scored ${correct}/${total}. Keep reviewing and retry the incorrect ones!`;
    banner.className = 'quiz-result-banner fail';
    banner.style.display = 'block';
  }
}

// Init
renderContent();
loadSidebar();
loadQuiz();
