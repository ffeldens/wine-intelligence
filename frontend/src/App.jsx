import { useMemo, useState } from 'react'
import { recommend, cellar, pairing } from './api.js'
import Wizard from './components/Wizard.jsx'
import PerfilPanel from './components/PerfilPanel.jsx'
import WineCard, { brl } from './components/WineCard.jsx'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState(null)
  const [data, setData] = useState(null)

  const handleSubmit = async (m, payload) => {
    setLoading(true)
    setError(null)
    setData(null)
    setMode(m)
    try {
      const res =
        m === 'descoberta' ? await recommend(payload)
          : m === 'prato' ? await pairing(payload)
            : await cellar(payload)
      setData(res)
    } catch (e) {
      setError(e.message || 'Falha ao consultar o sommelier.')
    } finally {
      setLoading(false)
    }
  }

  const perfil = data?.perfil_usuario

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-neutral-200 bg-cream/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🍷</span>
            <div>
              <h1 className="font-serif text-lg leading-none text-wine">Wine Intelligence</h1>
              <p className="text-[11px] tracking-wide text-neutral-500">Sommelier IA · TDP Wines</p>
            </div>
          </div>
          <span className="hidden text-xs text-neutral-400 sm:block">
            Recomendações do catálogo, ancoradas no seu paladar
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:py-8">
        <Hero />
        <Wizard onSubmit={handleSubmit} loading={loading} />

        {loading && <LoadingState mode={mode} />}
        {error && <ErrorState message={error} />}

        {data && !loading && (
          <div className="space-y-6">
            <PerfilPanel perfil={perfil} mode={mode} />
            {mode === 'adega' ? (
              <Adega data={data} />
            ) : (
              <Descoberta data={data} perfil={perfil} mode={mode} />
            )}
          </div>
        )}
      </main>

      <footer className="border-t border-neutral-200 py-6 text-center text-xs text-neutral-400">
        Wine Intelligence · protótipo MudAção para a TDP Wines · IA + catálogo real
      </footer>
    </div>
  )
}

function Hero() {
  return (
    <section className="relative overflow-hidden rounded-3xl bg-wine text-cream">
      {/* brilho dourado decorativo */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-16 -top-16 h-72 w-72 rounded-full opacity-30 blur-2xl"
        style={{ background: 'radial-gradient(circle, #c19a5b 0%, transparent 70%)' }}
      />
      <svg aria-hidden className="pointer-events-none absolute right-6 top-1/2 hidden -translate-y-1/2 opacity-20 sm:block" width="140" height="180" viewBox="0 0 140 180" fill="none" stroke="#f3e7d0" strokeWidth="2.5">
        <path d="M40 20 h60 a0 0 0 0 1 0 0 c0 30 -12 46 -30 52 c-18 -6 -30 -22 -30 -52z" />
        <line x1="70" y1="72" x2="70" y2="130" />
        <line x1="44" y1="130" x2="96" y2="130" />
      </svg>

      <div className="relative max-w-2xl px-6 py-10 sm:px-10 sm:py-14">
        <p className="text-[11px] uppercase tracking-[0.2em] text-gold">Sommelier virtual · TDP Wines</p>
        <h2 className="mt-3 font-serif text-3xl leading-tight sm:text-4xl">
          A garrafa certa para o seu momento — escolhida por IA, do catálogo TDP.
        </h2>
        <p className="mt-3 max-w-xl text-sm text-cream/80 sm:text-base">
          Descreva seu paladar, um prato ou um orçamento. O sommelier interpreta, cruza com o
          perfil sensorial de 161 rótulos e explica cada escolha — sem inventar nada fora do catálogo.
        </p>
        <div className="mt-5 flex flex-wrap gap-2 text-[11px]">
          {['Descoberta por paladar', 'Harmonização por prato', 'Adega por objetivo'].map((t) => (
            <span key={t} className="rounded-full bg-cream/10 px-3 py-1 text-cream/90">{t}</span>
          ))}
        </div>
      </div>
    </section>
  )
}

function Descoberta({ data, perfil, mode }) {
  const isPrato = mode === 'prato'
  const sel = data.selecao || []
  const desc = data.descobertas || []
  if (!sel.length) {
    return (
      <EmptyState
        title={data.aviso || 'Nenhum vinho encontrado.'}
        hint="Tente afrouxar os filtros (tipo, país ou orçamento) ou descrever o paladar com outras palavras."
      />
    )
  }
  return (
    <>
      <div>
        <h3 className="mb-3 font-serif text-xl text-ink">{isPrato ? 'Harmonizações' : 'Sua seleção'}</h3>
        <div className="space-y-4">
          {sel.map((item, i) => (
            <WineCard key={item.wine.id} item={item} rank={i + 1} userProfile={perfil?.sensory_profile} />
          ))}
        </div>
      </div>

      {desc.length > 0 && (
        <div>
          <h3 className="mb-1 font-serif text-xl text-ink">
            {isPrato ? 'Harmonizações surpreendentes' : 'Descobertas inteligentes'}
          </h3>
          <p className="mb-3 text-sm text-neutral-500">
            {isPrato
              ? 'Rótulos de regiões/uvas inesperadas que também casam com o prato.'
              : 'Rótulos fora do que você citou, mas que casam com seu paladar.'}
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {desc.map((d) => (
              <article key={d.wine.id} className="card p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="font-serif text-base text-ink">{d.wine.nome}</h4>
                    <p className="text-xs text-neutral-500">{d.wine.produtor} · {d.wine.pais}</p>
                  </div>
                  <span className="font-serif text-lg text-wine">{d.compatibilidade}%</span>
                </div>
                <p className="mt-2 text-xs italic text-gold-dark">{d.motivo}</p>
                <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-neutral-500">
                  {d.wine.uva && <span className="rounded-full bg-neutral-100 px-2 py-0.5">{d.wine.uva}</span>}
                  <span className="rounded-full bg-neutral-100 px-2 py-0.5">{brl(d.wine.preco)}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function Adega({ data }) {
  const baldes = (data.adega || []).filter((b) => b.garrafas?.length)
  const todas = useMemo(() => baldes.flatMap((b) => b.garrafas), [baldes])
  // Modo Compra: quantidade por garrafa (default 1), lista somável
  const [qtd, setQtd] = useState({})
  const [copiado, setCopiado] = useState(false)

  const getQ = (id) => (qtd[id] === undefined ? 1 : qtd[id])
  const setQ = (id, v) => setQtd((prev) => ({ ...prev, [id]: Math.max(0, v) }))

  const liveGarrafas = todas.reduce((s, g) => s + getQ(g.wine.id), 0)
  const liveValor = todas.reduce((s, g) => s + getQ(g.wine.id) * (g.preco || 0), 0)

  if (!baldes.length) {
    return (
      <EmptyState
        title={data.aviso || 'Não foi possível montar a adega.'}
        hint="Aumente o número de garrafas ou o orçamento, ou remova os filtros de tipo/país."
      />
    )
  }

  const copiarLista = () => {
    const linhas = todas
      .filter((g) => getQ(g.wine.id) > 0)
      .map((g) => {
        const n = getQ(g.wine.id)
        return `${n}× ${g.wine.nome} — ${brl(g.preco)}${n > 1 ? ` (${brl(n * g.preco)})` : ''}`
      })
    const txt = ['Adega — TDP Wines', '', ...linhas, '', `Total: ${liveGarrafas} garrafas · ${brl(liveValor)}`].join('\n')
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(txt).then(() => {
        setCopiado(true)
        setTimeout(() => setCopiado(false), 2000)
      })
    }
  }

  return (
    <>
      {/* Resumo (somável ao vivo) */}
      <section className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:flex">
            <Stat label="Garrafas" value={liveGarrafas} />
            <Stat label="Total" value={brl(liveValor)} />
            <Stat label="Orçamento" value={data.orcamento_total ? brl(data.orcamento_total) : 'Sem teto'} />
            {data.orcamento_total != null && (
              <Stat
                label="Restante"
                value={brl(data.orcamento_total - liveValor)}
                alert={data.orcamento_total - liveValor < 0}
              />
            )}
          </div>
          <button
            onClick={copiarLista}
            className="rounded-full border border-wine px-4 py-2 text-sm font-medium text-wine transition hover:bg-wine hover:text-cream"
          >
            {copiado ? '✓ Copiado' : 'Copiar lista'}
          </button>
        </div>
        {data.orcamento_total != null && (
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-neutral-100">
            <div
              className={`h-full rounded-full ${liveValor > data.orcamento_total ? 'bg-red-500' : 'bg-wine'}`}
              style={{ width: `${Math.min(100, Math.round((liveValor / data.orcamento_total) * 100))}%` }}
            />
          </div>
        )}
      </section>

      <div className="space-y-6">
        {baldes.map((b) => (
          <div key={b.objetivo}>
            <div className="mb-2 flex items-baseline justify-between">
              <h3 className="font-serif text-lg text-ink">{b.titulo}</h3>
              <span className="text-xs uppercase tracking-wide text-neutral-400">{b.garrafas.length} rótulos</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {b.garrafas.map((g) => {
                const n = getQ(g.wine.id)
                return (
                  <article
                    key={g.wine.id}
                    className={`card p-4 transition ${n === 0 ? 'opacity-50' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h4 className="font-serif text-base leading-tight text-ink">{g.wine.nome}</h4>
                        <p className="text-xs text-neutral-500">
                          {g.wine.produtor} · {g.wine.pais}
                          {g.wine.uva ? ` · ${g.wine.uva}` : ''}
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5 text-[11px] text-neutral-500">
                          {g.wine.tipo && <span className="rounded-full bg-neutral-100 px-2 py-0.5">{g.wine.tipo}</span>}
                          <span className="rounded-full bg-gold/10 px-2 py-0.5 text-gold-dark">{g.compatibilidade}% compat</span>
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="font-serif text-wine">{brl(g.preco)}</div>
                        {n > 1 && <div className="text-[11px] text-neutral-400">{brl(n * g.preco)}</div>}
                      </div>
                    </div>
                    <Stepper value={n} onChange={(v) => setQ(g.wine.id, v)} />
                  </article>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function Stepper({ value, onChange }) {
  const btn = 'flex h-7 w-7 items-center justify-center rounded-full border border-neutral-300 text-neutral-600 transition hover:border-wine hover:text-wine'
  return (
    <div className="mt-3 flex items-center gap-2 border-t border-neutral-100 pt-3">
      <span className="text-[11px] uppercase tracking-wide text-neutral-400">Qtd.</span>
      <button type="button" className={btn} onClick={() => onChange(value - 1)} aria-label="Menos">−</button>
      <span className="w-6 text-center font-medium tabular-nums text-ink">{value}</span>
      <button type="button" className={btn} onClick={() => onChange(value + 1)} aria-label="Mais">+</button>
    </div>
  )
}

function Stat({ label, value, alert }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-neutral-400">{label}</div>
      <div className={`font-serif text-lg ${alert ? 'text-red-600' : 'text-ink'}`}>{value}</div>
    </div>
  )
}

function EmptyState({ title, hint }) {
  return (
    <div className="card flex flex-col items-center gap-2 p-8 text-center">
      <span className="text-3xl">🍇</span>
      <p className="font-serif text-lg text-ink">{title}</p>
      <p className="max-w-sm text-sm text-neutral-500">{hint}</p>
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div className="card flex items-start gap-3 border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <span className="text-lg leading-none">⚠️</span>
      <div>
        <p className="font-medium">Não consegui completar agora.</p>
        <p className="mt-0.5 text-red-600/80">{message}</p>
      </div>
    </div>
  )
}

function LoadingState({ mode }) {
  const msg = mode === 'adega' ? 'Montando sua adega…' : mode === 'prato' ? 'Buscando as melhores harmonizações…' : 'O sommelier está provando o catálogo…'
  return (
    <div className="card flex items-center gap-3 p-5 text-sm text-neutral-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-300 border-t-wine" />
      {msg}
    </div>
  )
}
