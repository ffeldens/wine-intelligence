import RadarSensorial from './RadarSensorial.jsx'

export default function PerfilPanel({ perfil }) {
  if (!perfil) return null
  return (
    <section className="card bg-wine text-cream">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
        <div className="shrink-0 sm:w-56">
          <RadarSensorial profile={perfil.sensory_profile} size={200} color="#c19a5b" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] uppercase tracking-wide text-gold">Seu perfil de paladar</p>
          <p className="mt-1 font-serif text-lg leading-snug">{perfil.resumo}</p>
          {perfil.inferencia && (
            <p className="mt-2 inline-block rounded-full bg-cream/10 px-3 py-1 text-sm text-gold">
              {perfil.inferencia}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
            {(perfil.regioes_ou_uvas || []).map((r) => (
              <span key={r} className="rounded-full bg-cream/10 px-2 py-0.5">{r}</span>
            ))}
          </div>
          {perfil.evitar?.length > 0 && (
            <p className="mt-2 text-xs text-cream/70">
              Evita: {perfil.evitar.join(' · ')}
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
