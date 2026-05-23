const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
let sessionId = '';

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

function addMessage(role, content, info = '') {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `<div class="msg-content">${escapeHtml(content)}</div>${info ? `<div class="msg-info">${info}</div>` : ''}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = 'typing-indicator';
  div.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = '';
  addMessage('user', text);
  showTyping();
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    hideTyping();
    if (!res.ok) { addMessage('assistant', `Error: ${res.statusText}`); return; }
    const data = await res.json();
    sessionId = data.session_id || sessionId;
    let response = data.response || '(no response)';
    let info = `${data.model || ''} · ${(data.usage?.total_tokens || 0).toLocaleString()} tokens`;
    addMessage('assistant', response, info);
    updateStatus();
  } catch (e) {
    hideTyping();
    addMessage('assistant', `Connection error: ${e.message}`);
  }
}

async function resetConversation() {
  await fetch('/api/reset', { method: 'POST' });
  messagesEl.innerHTML = '';
  sessionId = '';
  updateStatus();
}

async function updateStatus() {
  try {
    const status = await fetch('/api/status').then(r => r.json());
    document.getElementById('s-model').textContent = status.model || '-';
    document.getElementById('s-provider').textContent = status.provider || '-';
    document.getElementById('s-mode').textContent = status.active_mode || 'agentic';
    document.getElementById('model-indicator').textContent =
      `${status.model || '?'} · ${status.provider || '?'}`;
  } catch(e) {}
}

updateStatus();
