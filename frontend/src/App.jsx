import { useState } from 'react'
import { recommend, cellar } from './api.js'
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
      const res = m === 'descoberta' ? await recommend(payload) : await cellar(payload)
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
      <header className="border-b border-neutral-200 bg-cream/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
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

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <div className="max-w-2xl">
          <h2 className="font-serif text-2xl text-ink sm:text-3xl">
            Descreva o que você gosta. Deixe a IA encontrar sua garrafa.
          </h2>
          <p className="mt-2 text-sm text-neutral-500">
            O sommelier interpreta seu paladar, cruza com o perfil sensorial de cada rótulo da
            TDP e explica por que cada indicação combina — sem inventar nada fora do catálogo.
          </p>
        </div>

        <Wizard onSubmit={handleSubmit} loading={loading} />

        {loading && <LoadingState mode={mode} />}
        {error && (
          <div className="card border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {data && !loading && (
          <div className="space-y-6">
            <PerfilPanel perfil={perfil} />
            {mode === 'descoberta' ? (
              <Descoberta data={data} perfil={perfil} />
            ) : (
              <Adega data={data} />
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

function Descoberta({ data, perfil }) {
  const sel = data.selecao || []
  const desc = data.descobertas || []
  if (!sel.length) {
    return <p className="text-sm text-neutral-500">{data.aviso || 'Nenhum vinho encontrado.'}</p>
  }
  return (
    <>
      <div>
        <h3 className="mb-3 font-serif text-xl text-ink">Sua seleção</h3>
        <div className="space-y-4">
          {sel.map((item, i) => (
            <WineCard key={item.wine.id} item={item} rank={i + 1} userProfile={perfil?.sensory_profile} />
          ))}
        </div>
      </div>

      {desc.length > 0 && (
        <div>
          <h3 className="mb-1 font-serif text-xl text-ink">Descobertas inteligentes</h3>
          <p className="mb-3 text-sm text-neutral-500">
            Rótulos fora do que você citou, mas que casam com seu paladar.
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
  if (!baldes.length) {
    return <p className="text-sm text-neutral-500">{data.aviso || 'Não foi possível montar a adega.'}</p>
  }
  return (
    <>
      {/* Resumo do orçamento */}
      <section className="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="flex gap-6 text-sm">
          <Stat label="Garrafas" value={`${data.garrafas_selecionadas}/${data.garrafas_alvo}`} />
          <Stat label="Total" value={brl(data.total)} />
          <Stat label="Orçamento" value={data.orcamento_total ? brl(data.orcamento_total) : 'Sem teto'} />
          {data.orcamento_total != null && <Stat label="Restante" value={brl(data.restante)} />}
        </div>
        {data.orcamento_total != null && (
          <div className="h-2 w-full max-w-[220px] overflow-hidden rounded-full bg-neutral-100">
            <div
              className="h-full rounded-full bg-wine"
              style={{ width: `${Math.min(100, Math.round((data.total / data.orcamento_total) * 100))}%` }}
            />
          </div>
        )}
      </section>

      <div className="space-y-6">
        {baldes.map((b) => (
          <div key={b.objetivo}>
            <div className="mb-2 flex items-baseline justify-between">
              <h3 className="font-serif text-lg text-ink">{b.titulo}</h3>
              <span className="text-sm text-neutral-500">
                {b.garrafas.length} · {brl(b.subtotal)}
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {b.garrafas.map((g) => (
                <article key={g.wine.id} className="card flex items-start justify-between gap-3 p-4">
                  <div className="min-w-0">
                    <h4 className="font-serif text-base leading-tight text-ink">{g.wine.nome}</h4>
                    <p className="text-xs text-neutral-500">
                      {g.wine.produtor} · {g.wine.pais}
                      {g.wine.uva ? ` · ${g.wine.uva}` : ''}
                    </p>
                    <div className="mt-1.5 flex gap-1.5 text-[11px] text-neutral-500">
                      {g.wine.tipo && <span className="rounded-full bg-neutral-100 px-2 py-0.5">{g.wine.tipo}</span>}
                      <span className="rounded-full bg-gold/10 px-2 py-0.5 text-gold-dark">{g.compatibilidade}% compat</span>
                    </div>
                  </div>
                  <span className="shrink-0 font-serif text-wine">{brl(g.preco)}</span>
                </article>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-neutral-400">{label}</div>
      <div className="font-serif text-lg text-ink">{value}</div>
    </div>
  )
}

function LoadingState({ mode }) {
  return (
    <div className="card flex items-center gap-3 p-5 text-sm text-neutral-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-300 border-t-wine" />
      {mode === 'adega' ? 'Montando sua adega…' : 'O sommelier está provando o catálogo…'}
    </div>
  )
}
