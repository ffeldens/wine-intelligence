import RadarSensorial from './RadarSensorial.jsx'

export const brl = (v) =>
  typeof v === 'number'
    ? v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    : '—'

const COMPONENTES = [
  ['sensorial', 'Sensorial'],
  ['produtor', 'Produtor'],
  ['custo_beneficio', 'Custo-benef.'],
  ['orcamento', 'Orçamento'],
  ['diversidade', 'Diversidade'],
]

function Bar({ label, value }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 shrink-0 text-[11px] text-neutral-500">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-neutral-100">
        <div className="h-full rounded-full bg-gold" style={{ width: `${Math.round((value || 0) * 100)}%` }} />
      </div>
      <span className="w-8 text-right text-[11px] tabular-nums text-neutral-400">
        {Math.round((value || 0) * 100)}
      </span>
    </div>
  )
}

// item: { wine, compatibilidade, componentes, justificativa }  (rank opcional)
export default function WineCard({ item, rank, userProfile }) {
  const w = item.wine
  return (
    <article className="card overflow-hidden">
      <div className="flex flex-col gap-4 p-5 sm:flex-row">
        {/* Coluna principal */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              {rank != null && (
                <span className="mb-1 inline-block rounded-full bg-wine/10 px-2 py-0.5 text-[11px] font-semibold text-wine">
                  Escolha #{rank}
                </span>
              )}
              <h3 className="font-serif text-lg leading-tight text-ink">{w.nome}</h3>
              <p className="mt-0.5 text-sm text-neutral-500">
                {w.produtor} · {w.regiao || w.pais}
                {w.safra && w.safra !== 'NV' ? ` · ${w.safra}` : ''}
              </p>
            </div>
            <div className="shrink-0 text-right">
              <div className="font-serif text-2xl text-wine">{item.compatibilidade}%</div>
              <div className="text-[10px] uppercase tracking-wide text-neutral-400">compatível</div>
            </div>
          </div>

          <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
            {w.tipo && <Tag>{w.tipo}</Tag>}
            {w.uva && <Tag>{w.uva}</Tag>}
            <Tag className="border-gold/40 bg-gold/10 text-gold-dark">{brl(w.preco)}</Tag>
            {w.pontuacoes && <Tag className="border-wine/30 bg-wine/5 text-wine">★ {w.pontuacoes}</Tag>}
          </div>

          {item.justificativa && (
            <p className="mt-3 border-l-2 border-gold/50 pl-3 text-sm italic leading-relaxed text-neutral-600">
              {item.justificativa}
            </p>
          )}

          {w.harmonizacao && (
            <p className="mt-2 text-xs text-neutral-500">
              <span className="font-semibold text-neutral-600">Harmoniza:</span> {w.harmonizacao}
            </p>
          )}

          {item.componentes && (
            <div className="mt-3 space-y-1">
              {COMPONENTES.map(([k, label]) =>
                item.componentes[k] != null ? <Bar key={k} label={label} value={item.componentes[k]} /> : null,
              )}
            </div>
          )}
        </div>

        {/* Radar */}
        {w.sensory_profile && (
          <div className="flex shrink-0 flex-col items-center sm:w-52">
            <RadarSensorial profile={w.sensory_profile} compare={userProfile} size={200} />
            {userProfile && (
              <div className="mt-1 flex items-center gap-3 text-[10px] text-neutral-400">
                <span className="flex items-center gap-1">
                  <i className="inline-block h-2 w-2 rounded-full bg-wine" /> vinho
                </span>
                <span className="flex items-center gap-1">
                  <i className="inline-block h-2 w-2 rounded-full bg-gold" /> seu paladar
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  )
}

function Tag({ children, className = '' }) {
  return (
    <span className={`rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-neutral-600 ${className}`}>
      {children}
    </span>
  )
}
