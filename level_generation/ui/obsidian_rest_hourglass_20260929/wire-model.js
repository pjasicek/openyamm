// Preserved first motion proof for the before/after comparison.
function wireModel(id) {
  const column = x => `<g transform="translate(${x} 0)">
    <path d="M-5 36 Q-3 62-4 78 Q-6 88-6 95 Q-6 102-4 112 Q-3 128-5 154 L5 154
      Q3 128 4 112 Q6 102 6 95 Q6 88 4 78 Q3 62 5 36Z" fill="url(#stone-${id})" stroke="#151a17"/>
    ${[39,50,89,101,140,151].map(y=>`<ellipse cx="0" cy="${y}" rx="6.8" ry="2.5" fill="url(#gold-${id})" stroke="#30271b" stroke-width=".7"/>`).join('')}
    <path d="M-1 55L-2 82M-2 108L-1 135" stroke="#a9a897" stroke-width=".7" opacity=".5"/>
  </g>`;
  const cap = flip => `<g transform="${flip ? 'rotate(180 60 95)' : ''}">
    <path d="M21 20Q60 9 99 20L98 32Q60 42 22 32Z" fill="url(#stone-${id})" stroke="#746747"/>
    <path d="M21 23Q60 32 99 23L98 30Q60 40 22 30Z" fill="url(#gold-${id})" stroke="#332b1b"/>
    <ellipse cx="60" cy="20" rx="39" ry="8" fill="url(#stone-${id})" stroke="#c2a46c" stroke-width=".9"/>
    <ellipse cx="60" cy="19" rx="33" ry="5.2" fill="none" stroke="#6e5a39" stroke-width=".6"/>
    <path d="M32 16L34 34M85 15L84 35" stroke="#171b18" stroke-width="5"/>
    ${[34,84].map(x=>`<circle cx="${x}" cy="28" r="2.4" fill="url(#gold-${id})" stroke="#3c301d" stroke-width=".6"/>`).join('')}
    <path d="M60 17L64 21L60 25L56 21Z" fill="url(#gold-${id})" stroke="#51422a" stroke-width=".7"/>
    <path d="M45 27l5 1m24-1 4-.6M30 30l5 1m33 1 6-.2" stroke="#e8d39a" stroke-width=".45" opacity=".65"/>
  </g>`;
  return `<svg viewBox="0 0 120 190" role="img" aria-label="Stable hourglass with animated sand">
  <defs>
    <linearGradient id="gold-${id}"><stop stop-color="#332b1d"/><stop offset=".19" stop-color="#8b7040"/>
      <stop offset=".34" stop-color="#d3b77a"/><stop offset=".48" stop-color="#766039"/>
      <stop offset=".67" stop-color="#cbb17a"/><stop offset=".86" stop-color="#6b522e"/><stop offset="1" stop-color="#2b281e"/></linearGradient>
    <linearGradient id="stone-${id}"><stop stop-color="#111a16"/><stop offset=".29" stop-color="#51584c"/>
      <stop offset=".45" stop-color="#222e26"/><stop offset=".72" stop-color="#141f19"/><stop offset="1" stop-color="#3d4338"/></linearGradient>
    <linearGradient id="glass-${id}"><stop stop-color="#91a9a5" stop-opacity=".36"/><stop offset=".18" stop-color="#dce9e3" stop-opacity=".13"/>
      <stop offset=".36" stop-color="#152921" stop-opacity=".09"/><stop offset=".73" stop-color="#9fb3af" stop-opacity=".12"/>
      <stop offset=".91" stop-color="#e7eee5" stop-opacity=".33"/><stop offset="1" stop-color="#86a29a" stop-opacity=".38"/></linearGradient>
    <linearGradient id="sand-${id}"><stop stop-color="#857449"/><stop offset=".38" stop-color="#ddd0a1"/>
      <stop offset=".61" stop-color="#c7b782"/><stop offset="1" stop-color="#938157"/></linearGradient>
    <pattern id="grain-${id}" width="3.1" height="2.7" patternUnits="userSpaceOnUse">
      <circle cx=".6" cy=".7" r=".27" fill="#fff1c6" opacity=".32"/><circle cx="2.2" cy="1.9" r=".24" fill="#574c30" opacity=".3"/>
    </pattern>
    <path id="vessel-${id}" d="M37 39C31 55 39 75 55 89Q60 94 55 101C39 115 31 135 37 151
      Q60 157 83 151C89 135 81 115 65 101Q60 94 65 89C81 75 89 55 83 39Q60 34 37 39Z"/>
    <clipPath id="inside-${id}"><use href="#vessel-${id}"/></clipPath>
    <clipPath id="upper-${id}"><rect class="upper-limit" x="25" y="39" width="70" height="56"/></clipPath>
  </defs>
  <g class="rigid-model">
    <g class="fixed-back"><path d="M57 37L57 153L63 153L63 37" fill="#111912" opacity=".6"/>
      <use href="#vessel-${id}" fill="url(#glass-${id})" stroke="#6f8981" stroke-width=".8"/>
    </g>
    <g clip-path="url(#inside-${id})" class="sand-layer">
      <g clip-path="url(#upper-${id})">
        <path d="M87 39Q73.5 87 60 95Q46.5 87 33 39V33H87Z" fill="url(#sand-${id})"/>
        <path d="M87 39Q73.5 87 60 95Q46.5 87 33 39V33H87Z" fill="url(#grain-${id})"/>
      </g>
      <path class="sand-shape" fill="url(#sand-${id})"/>
      <path class="sand-grain" fill="url(#grain-${id})"/>
      <path class="stream" fill="none" stroke="#e3d5a9" stroke-width="1"/>
      <path class="stream-grains" fill="none" stroke="#fff0c3" stroke-width=".6" stroke-dasharray=".6 3.7"/>
    </g>
    <g class="fixed-front">
      <use href="#vessel-${id}" fill="url(#glass-${id})" stroke="#adb8a3" stroke-opacity=".52" stroke-width=".65"/>
      <path d="M40 45C36 60 43 74 51 83M39 137C36 125 44 110 52 104" fill="none" stroke="#dae6df" stroke-opacity=".63" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M79 46C84 62 74 77 68 84M80 139C84 124 77 114 69 105" fill="none" stroke="#d1ddd4" stroke-opacity=".4" stroke-width="2.3" stroke-linecap="round"/>
      ${column(25)}${column(95)}${cap(false)}${cap(true)}
    </g>
  </g></svg>`;
}

