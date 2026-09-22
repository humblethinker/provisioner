const fallbackRoles = [
  { company: 'OpenAI', title: 'Product Manager, Developer Experience', place: 'San Francisco · Hybrid', score: 94, time: 'Today', logo: '◎', tone: 'openai', fresh: true },
  { company: 'Anthropic', title: 'Product Manager, Enterprise', place: 'San Francisco · Hybrid', score: 91, time: 'Today', logo: 'A', tone: 'anthropic', fresh: true },
  { company: 'Harvey', title: 'Senior Product Manager', place: 'San Francisco · On-site', score: 87, time: 'Yesterday', logo: 'H', tone: 'harvey' },
  { company: 'Cohere', title: 'Product Lead, Platform', place: 'Remote · North America', score: 82, time: 'Yesterday', logo: 'C', tone: 'cohere' },
  { company: 'Perplexity', title: 'Product Manager, Search', place: 'San Francisco · Hybrid', score: 79, time: '2d ago', logo: 'P', tone: 'perplexity' }
];

let roles = fallbackRoles;
const list = document.querySelector('#roleList');
function renderRoles() { list.innerHTML = roles.map((role, index) => `<article class="role ${index === 0 ? 'current' : ''}" data-index="${index}">
  <div class="company-logo ${role.tone || role.company.toLowerCase()}">${role.logo || role.company[0]}</div><div class="role-copy"><div class="role-company">${role.company}${role.fresh ? '<span class="tiny-new">NEW</span>' : ''}</div><h3>${role.title}</h3><p>${role.place || role.location}</p></div><div class="role-side"><strong>${role.score || role.match_score}%</strong><small>${role.time || 'Live'}</small></div></article>`).join('');
document.querySelectorAll('.role').forEach(card => card.addEventListener('click', () => {
  document.querySelector('.role.current')?.classList.remove('current'); card.classList.add('current');
  const role = roles[card.dataset.index];
  document.querySelector('.company-heading p').textContent = role.company;
  document.querySelector('.company-heading span').textContent = role.place || role.location;
  document.querySelector('.company-heading .company-logo').className = `company-logo ${role.tone || role.company.toLowerCase()}`;
  document.querySelector('.company-heading .company-logo').textContent = role.logo || role.company[0];
  document.querySelector('.detail-card > h2').innerHTML = role.title.replace(', ', ',<br />');
  document.querySelector('.match-score strong').textContent = role.score || role.match_score;
  if (role.description) document.querySelector('.description > p:not(.label)').textContent = role.description.slice(0, 340);
})); }
renderRoles();

const toast = document.querySelector('#toast');
function showToast(message) { toast.textContent = message; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 2600); }
async function scanJobs() { const button = document.querySelector('#scanButton'); button.disabled = true; button.textContent = '↻ Queueing scan…'; try { const response = await fetch('/api/scans', { method: 'POST' }); if (!response.ok) throw new Error('scan failed'); showToast('Browser-agent scan queued. It will refresh the feed when complete.'); } catch { showToast('Could not contact Scout. Start it with docker compose up --build.'); } finally { button.disabled = false; button.textContent = '↻ Scan careers sites'; } }
document.querySelector('#scanButton').addEventListener('click', scanJobs);
document.querySelector('.save').addEventListener('click', e => { e.currentTarget.classList.toggle('saved'); e.currentTarget.textContent = e.currentTarget.classList.contains('saved') ? '♥' : '♡'; showToast(e.currentTarget.classList.contains('saved') ? 'Role saved to your tracker.' : 'Role removed from saved.'); });
document.querySelector('#tailorButton').addEventListener('click', () => document.querySelector('#modal').classList.add('visible'));
document.querySelector('#closeModal').addEventListener('click', () => document.querySelector('#modal').classList.remove('visible'));
document.querySelector('#modal').addEventListener('click', e => { if (e.target.id === 'modal') e.currentTarget.classList.remove('visible'); });
document.querySelector('#studioButton').addEventListener('click', async () => { const current = document.querySelector('.role.current'); const job = roles[current?.dataset.index || 0]; document.querySelector('#modal').classList.remove('visible'); try { const response = await fetch('/api/applications', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job_id: job.id }) }); if (!response.ok) throw new Error('queue failed'); showToast('Resume queued. The finished PDF will appear after review generation.'); } catch { showToast('Could not queue the PDF. Start the application worker and select a scanned role.'); } });
document.querySelector('#applyButton').addEventListener('click', () => showToast('Application link copied — ready when you are.'));
document.querySelector('#readMore').addEventListener('click', e => { e.currentTarget.closest('.description').classList.toggle('expanded'); e.currentTarget.innerHTML = e.currentTarget.closest('.description').classList.contains('expanded') ? 'Show less <span>↑</span>' : 'Read full description <span>↓</span>'; });
