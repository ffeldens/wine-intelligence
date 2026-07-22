// Cliente da API. Em produção o nginx serve o SPA e proxya /api → backend;
// em dev o Vite proxya /api → localhost:8004. Logo, base same-origin ("").
const BASE = import.meta.env.VITE_API_BASE || ''

async function post(path, body) {
  const r = await fetch(`${BASE}/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const txt = await r.text().catch(() => '')
    throw new Error(`Erro ${r.status}${txt ? `: ${txt.slice(0, 200)}` : ''}`)
  }
  return r.json()
}

export const recommend = (body) => post('/recommend', body)
export const cellar = (body) => post('/cellar', body)
export const pairing = (body) => post('/pairing', body)
export const getStats = () => fetch(`${BASE}/api/stats`).then((r) => r.json())
