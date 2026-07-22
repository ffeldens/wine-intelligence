const AXES = [
  ['acidez', 'Acidez'],
  ['corpo', 'Corpo'],
  ['mineralidade', 'Mineral.'],
  ['madeira', 'Madeira'],
  ['fruta', 'Fruta'],
  ['persistencia', 'Persist.'],
  ['complexidade', 'Complex.'],
  ['guarda', 'Guarda'],
]

// Radar de 8 eixos (0-10). Aceita um perfil OU dois (usuário vs vinho) p/ overlay.
export default function RadarSensorial({ profile, compare, size = 240, color = '#6b1f2a' }) {
  if (!profile) return null
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 34
  const n = AXES.length

  const point = (i, val) => {
    const ang = (Math.PI * 2 * i) / n - Math.PI / 2
    const rr = (Math.max(0, Math.min(10, val)) / 10) * r
    return [cx + rr * Math.cos(ang), cy + rr * Math.sin(ang)]
  }
  const polyOf = (prof) =>
    AXES.map(([k], i) => point(i, Number(prof?.[k] ?? 0)).join(',')).join(' ')

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto">
      {[2, 4, 6, 8, 10].map((g) => (
        <polygon
          key={g}
          points={AXES.map((_, i) => point(i, g).join(',')).join(' ')}
          fill="none"
          stroke="#e7e0d5"
          strokeWidth="1"
        />
      ))}
      {AXES.map((_, i) => {
        const [x, y] = point(i, 10)
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e7e0d5" />
      })}

      {compare && (
        <polygon points={polyOf(compare)} fill="#c19a5b" fillOpacity="0.18" stroke="#c19a5b" strokeWidth="1.5" />
      )}
      <polygon points={polyOf(profile)} fill={color} fillOpacity="0.28" stroke={color} strokeWidth="2" />

      {AXES.map(([k, label], i) => {
        const [x, y] = point(i, 11.9)
        return (
          <text key={k} x={x} y={y} fontSize="9.5" textAnchor="middle" dominantBaseline="middle" fill="#7a7268">
            {label}
          </text>
        )
      })}
    </svg>
  )
}
