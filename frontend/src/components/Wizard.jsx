import { useState } from 'react'

const TIPOS = ['', 'tinto', 'branco', 'rosé', 'espumante', 'fortificado']
const PAISES = ['', 'França', 'Itália', 'Portugal', 'Espanha', 'Chile', 'Argentina', 'África do Sul', 'Brasil']

const EXEMPLOS = [
  'Gosto de Chablis, Champagne Nature e brancos minerais e secos; evito muito amadeirado.',
  'Tintos encorpados da Toscana e do Douro, com boa guarda e taninos firmes.',
  'Malbec argentino frutado para o dia a dia, algo versátil para carnes.',
]

export default function Wizard({ onSubmit, loading }) {
  const [mode, setMode] = useState('descoberta')
  const [preferencias, setPreferencias] = useState('')
  const [favoritos, setFavoritos] = useState('')
  const [tipo, setTipo] = useState('')
  const [pais, setPais] = useState('')
  const [orcamento, setOrcamento] = useState('')
  const [qtd, setQtd] = useState(4)
  const [orcTotal, setOrcTotal] = useState('')
  const [garrafas, setGarrafas] = useState(6)

  const submit = (e) => {
    e.preventDefault()
    if (!preferencias.trim() || loading) return
    const favArr = favoritos.split(',').map((s) => s.trim()).filter(Boolean)
    const comum = {
      preferencias,
      favoritos: favArr.length ? favArr : null,
      tipo: tipo || null,
      pais: pais || null,
    }
    if (mode === 'descoberta') {
      onSubmit('descoberta', { ...comum, orcamento: orcamento ? Number(orcamento) : null, qtd: Number(qtd) })
    } else {
      onSubmit('adega', { ...comum, orcamento_total: orcTotal ? Number(orcTotal) : null, garrafas: Number(garrafas) })
    }
  }

  return (
    <form onSubmit={submit} className="card p-5 sm:p-6">
      {/* Toggle de modo */}
      <div className="mb-5 inline-flex rounded-full bg-neutral-100 p-1 text-sm">
        {[
          ['descoberta', 'Descoberta'],
          ['adega', 'Adega pessoal'],
        ].map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setMode(k)}
            className={`rounded-full px-4 py-1.5 font-medium transition ${
              mode === k ? 'bg-wine text-cream shadow' : 'text-neutral-500 hover:text-wine'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div>
        <label className="label">Descreva seu paladar</label>
        <textarea
          className="field min-h-[92px] resize-y"
          placeholder="Ex.: gosto de brancos secos e minerais, Chablis, Champagne Nature…"
          value={preferencias}
          onChange={(e) => setPreferencias(e.target.value)}
        />
        <div className="mt-2 flex flex-wrap gap-1.5">
          {EXEMPLOS.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setPreferencias(ex)}
              className="rounded-full border border-neutral-200 px-2.5 py-1 text-[11px] text-neutral-500 transition hover:border-wine hover:text-wine"
            >
              {ex.slice(0, 42)}…
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4">
        <label className="label">Vinhos favoritos (opcional, separados por vírgula)</label>
        <input
          className="field"
          placeholder="Ex.: William Fèvre Chablis, Ruinart Blanc de Blancs"
          value={favoritos}
          onChange={(e) => setFavoritos(e.target.value)}
        />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label className="label">Tipo</label>
          <select className="field" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPOS.map((t) => (
              <option key={t} value={t}>{t || 'Qualquer'}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">País</label>
          <select className="field" value={pais} onChange={(e) => setPais(e.target.value)}>
            {PAISES.map((p) => (
              <option key={p} value={p}>{p || 'Qualquer'}</option>
            ))}
          </select>
        </div>

        {mode === 'descoberta' ? (
          <>
            <div>
              <label className="label">Orçamento/garrafa</label>
              <input className="field" type="number" min="0" placeholder="R$" value={orcamento} onChange={(e) => setOrcamento(e.target.value)} />
            </div>
            <div>
              <label className="label">Qtd. sugestões</label>
              <input className="field" type="number" min="1" max="12" value={qtd} onChange={(e) => setQtd(e.target.value)} />
            </div>
          </>
        ) : (
          <>
            <div>
              <label className="label">Orçamento total</label>
              <input className="field" type="number" min="0" placeholder="R$ (vazio = sem teto)" value={orcTotal} onChange={(e) => setOrcTotal(e.target.value)} />
            </div>
            <div>
              <label className="label">Nº de garrafas</label>
              <input className="field" type="number" min="2" max="24" value={garrafas} onChange={(e) => setGarrafas(e.target.value)} />
            </div>
          </>
        )}
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <p className="text-xs text-neutral-400">
          {mode === 'descoberta'
            ? 'Recomenda rótulos do catálogo TDP com % de compatibilidade e justificativa.'
            : 'Monta uma adega por objetivo (consumo, ocasiões, guarda, experimentação).'}
        </p>
        <button type="submit" className="btn-wine" disabled={loading || !preferencias.trim()}>
          {loading ? 'Analisando…' : mode === 'descoberta' ? 'Descobrir vinhos' : 'Montar adega'}
        </button>
      </div>
    </form>
  )
}
