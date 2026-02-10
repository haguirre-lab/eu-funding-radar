import { useState, useMemo, useEffect } from "react";

// ─── Sample data generator (replace with real data from your Python script) ───
const SAMPLE_DATA = [
  { id: "HORIZON-CL5-2025-D4-01", title: "Climate neutral and smart cities - Demonstrating innovative nature-based solutions in cities", description: "Support for cities to implement innovative NBS for climate adaptation and mitigation. Focus on urban greening, biodiversity, and ecosystem services.", status: "Open", deadline: "18/09/2025", url: "#", programme: "Horizon Europe", budget: "8,000,000 - 10,000,000", action_type: "Innovation Action", call_id: "HORIZON-MISS-2025-CIT-01", tags: "climate, cities, NBS", source: "EU", relevance_level: "MUY ALTA", relevance_note: "Bilbao es ciudad Mission de neutralidad climática 2030. Acceso prioritario vía NetZeroCities." },
  { id: "HORIZON-CL5-2025-D4-02", title: "Sustainable urban mobility planning and implementation in European cities", description: "Support for integrated sustainable urban mobility plans with focus on zero emission zones and active mobility infrastructure.", status: "Open", deadline: "05/11/2025", url: "#", programme: "Horizon Europe", budget: "4,000,000 - 6,000,000", action_type: "Research & Innovation", call_id: "HORIZON-MISS-2025-CIT-02", tags: "mobility, transport", source: "EU", relevance_level: "MUY ALTA", relevance_note: "Bilbao es nodo TEN-T. Metro, tranvía, BizkaiBus. Proyecto SuperIsla." },
  { id: "LIFE-2025-CET-LOCAL", title: "LIFE Clean Energy Transition - Local energy communities", description: "Support for local and regional authorities to establish and scale up renewable energy communities.", status: "Open", deadline: "12/11/2025", url: "#", programme: "LIFE", budget: "1,500,000", action_type: "Standard Action Projects", call_id: "LIFE-2025-CET", tags: "energy, communities", source: "EU", relevance_level: "ALTA", relevance_note: "Comunidades energéticas en desarrollo (Otxarkoaga, Txurdinaga)." },
  { id: "CEF-T-2025-SUST", title: "CEF Transport - Sustainable urban nodes on the TEN-T network", description: "Co-financing for sustainable transport infrastructure in urban nodes of the TEN-T network.", status: "Forthcoming", deadline: "20/01/2026", url: "#", programme: "CEF", budget: "15,000,000 - 25,000,000", action_type: "Works", call_id: "CEF-T-2025-SUSTMOB", tags: "transport, TEN-T", source: "EU", relevance_level: "MUY ALTA", relevance_note: "Bilbao es nodo TEN-T. Infraestructuras de transporte elegibles." },
  { id: "INTERREG-SUDOE-2025-03", title: "INTERREG SUDOE - Cooperación climática ciudades atlánticas", description: "Programa de cooperación transnacional para adaptación al cambio climático en ciudades del arco atlántico.", status: "Open", deadline: "30/09/2025", url: "#", programme: "INTERREG", budget: "2,000,000", action_type: "Cooperation", call_id: "SOE4/P4/E0890", tags: "climate, cooperation", source: "EU", relevance_level: "ALTA", relevance_note: "Elegible SUDOE e INTERREG Atlantic. Socios potenciales: Burdeos, Oporto." },
  { id: "DIGITAL-2025-TWINS", title: "Digital Europe - Urban digital twins for climate simulation", description: "Deployment of digital twin technologies for urban planning and climate impact simulation.", status: "Open", deadline: "22/10/2025", url: "#", programme: "Digital Europe", budget: "3,000,000 - 5,000,000", action_type: "Deployment", call_id: "DIGITAL-2025-DEPLOY-04", tags: "digital twin, AI", source: "EU", relevance_level: "ALTA", relevance_note: "Proyecto BIM/GIS de Bilbao. Complementa estrategia digital." },
  { id: "EUI-IA-2025-INN", title: "European Urban Initiative - Innovative Actions 2025", description: "Acciones innovadoras urbanas para ciudades europeas. Temas: transición verde, digital y justa.", status: "Forthcoming", deadline: "15/03/2026", url: "#", programme: "URBACT", budget: "5,000,000", action_type: "Innovative Actions", call_id: "EUI-IA-2025", tags: "urban, innovation", source: "EU", relevance_level: "MUY ALTA", relevance_note: "EUI-IA financia proyectos urbanos innovadores. Bilbao como ciudad Mission es candidata ideal." },
  { id: "NEB-2025-REGEN", title: "New European Bauhaus - Regeneración urbana sostenible e inclusiva", description: "Proyectos que combinan sostenibilidad, estética y accesibilidad en regeneración de barrios.", status: "Open", deadline: "08/12/2025", url: "#", programme: "Horizon Europe", budget: "2,000,000 - 3,500,000", action_type: "Innovation Action", call_id: "HORIZON-MISS-2025-NEB", tags: "bauhaus, regeneration", source: "EU", relevance_level: "ALTA", relevance_note: "NEB combina sostenibilidad + diseño + inclusión. Ideal para regeneración urbana Bilbao." },
  { id: "BDNS-789012", title: "Programa de ayudas para la rehabilitación energética de edificios (PREE 5000)", description: "Entidades locales. Fondos PRTR. Regiones: Todo el territorio nacional", status: "Open", deadline: "30/12/2025", url: "#", programme: "IDAE", budget: "125,000,000.00 EUR", action_type: "Subvencion Nacional", call_id: "BDNS 789012", tags: "PRTR, eficiencia", source: "BDNS", relevance_level: "MUY ALTA", relevance_note: "" },
  { id: "BDNS-789234", title: "Incentivos al vehículo eléctrico y puntos de recarga MOVES IV", description: "Administraciones públicas, empresas, particulares. Fondos PRTR.", status: "Open", deadline: "31/12/2025", url: "#", programme: "IDAE", budget: "400,000,000.00 EUR", action_type: "Subvencion Nacional", call_id: "BDNS 789234", tags: "PRTR, movilidad", source: "BDNS", relevance_level: "ALTA", relevance_note: "" },
  { id: "BDNS-790111", title: "Subvenciones para proyectos de I+D en transición energética justa", description: "Empresas, centros tecnológicos, universidades. Fondos MINECO.", status: "Open", deadline: "15/10/2025", url: "#", programme: "CDTI", budget: "50,000,000.00 EUR", action_type: "Subvencion Nacional", call_id: "BDNS 790111", tags: "I+D, energía", source: "BDNS", relevance_level: "MEDIA", relevance_note: "" },
  { id: "BDNS-790555", title: "Ayudas para la restauración de ecosistemas degradados en entornos urbanos", description: "Entidades locales, comunidades autónomas. Fondos PIMA Adapta.", status: "Open", deadline: "20/11/2025", url: "#", programme: "MITECO", budget: "30,000,000.00 EUR", action_type: "Subvencion Nacional", call_id: "BDNS 790555", tags: "biodiversidad, adaptación", source: "BDNS", relevance_level: "ALTA", relevance_note: "" },
  { id: "EUS-34521", title: "Programa de ayudas para instalaciones de autoconsumo en edificios públicos", description: "EVE - Ente Vasco de la Energía", status: "Open", deadline: "31/10/2025", url: "#", programme: "EVE", budget: "", action_type: "Ayuda/Subvencion Euskadi", call_id: "34521", tags: "autoconsumo", source: "KontratazioA", relevance_level: "MUY ALTA", relevance_note: "" },
  { id: "EUS-34599", title: "Licitación obras de mejora de eficiencia energética en equipamientos municipales de Bilbao", description: "Ayuntamiento de Bilbao", status: "Open", deadline: "25/09/2025", url: "#", programme: "Ayto. Bilbao", budget: "", action_type: "Licitacion Euskadi", call_id: "34599", tags: "eficiencia", source: "KontratazioA", relevance_level: "MUY ALTA", relevance_note: "" },
  { id: "EUS-34678", title: "Subvenciones para proyectos de economía circular en empresas vascas", description: "Ihobe - Sociedad Pública de Gestión Ambiental", status: "Open", deadline: "15/12/2025", url: "#", programme: "Ihobe", budget: "", action_type: "Ayuda/Subvencion Euskadi", call_id: "34678", tags: "circular", source: "KontratazioA", relevance_level: "ALTA", relevance_note: "" },
  { id: "EUS-34701", title: "Programa de digitalización e innovación para municipios vascos (SPRI Berrikuntza)", description: "SPRI - Agencia Vasca de Desarrollo Empresarial", status: "Forthcoming", deadline: "28/02/2026", url: "#", programme: "SPRI", budget: "", action_type: "Ayuda/Subvencion Euskadi", call_id: "34701", tags: "digital, innovación", source: "KontratazioA", relevance_level: "ALTA", relevance_note: "" },
  { id: "EUS-34780", title: "Contrato de servicios para plan de movilidad sostenible comarcal Bizkaia", description: "Diputación Foral de Bizkaia", status: "Open", deadline: "10/10/2025", url: "#", programme: "DFB", budget: "", action_type: "Licitacion Euskadi", call_id: "34780", tags: "movilidad", source: "KontratazioA", relevance_level: "ALTA", relevance_note: "" },
];

const SOURCE_MAP = {
  EU: { label: "Europa", color: "#1d4ed8", bg: "#eff6ff", icon: "🇪🇺", border: "#bfdbfe" },
  BDNS: { label: "España", color: "#b45309", bg: "#fffbeb", icon: "🇪🇸", border: "#fde68a" },
  KontratazioA: { label: "Euskadi", color: "#047857", bg: "#ecfdf5", icon: "🏔️", border: "#6ee7b7" },
};

const REL_CONFIG = {
  "MUY ALTA": { color: "#15803d", bg: "#dcfce7", label: "Muy Alta", dot: "🟢" },
  "ALTA": { color: "#1d4ed8", bg: "#dbeafe", label: "Alta", dot: "🔵" },
  "MEDIA": { color: "#a16207", bg: "#fef9c3", label: "Media", dot: "🟡" },
  "INFO": { color: "#6b7280", bg: "#f3f4f6", label: "Info", dot: "⚪" },
};

const STATUS_CONFIG = {
  "Open": { color: "#15803d", bg: "#dcfce7", label: "Abierta" },
  "Forthcoming": { color: "#6d28d9", bg: "#ede9fe", label: "Próxima" },
  "Unknown": { color: "#6b7280", bg: "#f3f4f6", label: "Info" },
};

const PROGRAMMES = ["Horizon Europe", "LIFE", "CEF", "Digital Europe", "INTERREG", "URBACT", "Innovation Fund"];

function getSourceKey(call) {
  if (call.source === "BDNS") return "BDNS";
  if (call.source === "KontratazioA") return "KontratazioA";
  return "EU";
}

function daysUntilDeadline(deadline) {
  if (!deadline) return null;
  try {
    const [d, m, y] = deadline.split("/");
    const dt = new Date(+y, +m - 1, +d);
    const now = new Date();
    return Math.ceil((dt - now) / (1000 * 60 * 60 * 24));
  } catch { return null; }
}

function Badge({ children, color, bg, border, small }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: small ? "1px 7px" : "2px 10px",
      borderRadius: 6, fontSize: small ? 10 : 11, fontWeight: 700,
      color, background: bg, border: `1px solid ${border || bg}`,
      whiteSpace: "nowrap", lineHeight: 1.6,
    }}>{children}</span>
  );
}

function CallCard({ call, isNew }) {
  const src = SOURCE_MAP[getSourceKey(call)];
  const rel = REL_CONFIG[call.relevance_level] || REL_CONFIG["INFO"];
  const st = STATUS_CONFIG[call.status] || STATUS_CONFIG["Unknown"];
  const days = daysUntilDeadline(call.deadline);
  const urgent = days !== null && days <= 30 && days >= 0;

  return (
    <div style={{
      background: "#fff",
      borderRadius: 12,
      border: `1px solid ${isNew ? "#fca5a5" : "#e5e7eb"}`,
      padding: "16px 20px",
      transition: "all 0.2s",
      position: "relative",
      overflow: "hidden",
      boxShadow: isNew ? "0 0 0 1px #fca5a5" : "none",
    }}
      onMouseEnter={e => { e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.08)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = isNew ? "0 0 0 1px #fca5a5" : "none"; e.currentTarget.style.transform = "none"; }}
    >
      {/* Source stripe */}
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 4, background: src.color, borderRadius: "12px 0 0 12px" }} />

      {/* Top row: badges */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8, paddingLeft: 8 }}>
        <Badge color={src.color} bg={src.bg} border={src.border}>{src.icon} {src.label}</Badge>
        <Badge color={st.color} bg={st.bg}>{st.label}</Badge>
        {call.programme && <Badge color="#7c3aed" bg="#f5f3ff" border="#ddd6fe">{call.programme}</Badge>}
        <Badge color={rel.color} bg={rel.bg}>{rel.dot} {rel.label}</Badge>
        {isNew && <Badge color="#dc2626" bg="#fee2e2" border="#fca5a5">🆕 Nueva</Badge>}
        {urgent && <Badge color="#dc2626" bg="#fef2f2" border="#fecaca" small>⏰ {days}d</Badge>}
      </div>

      {/* Title */}
      <div style={{ paddingLeft: 8 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#1e293b", lineHeight: 1.45, margin: 0, marginBottom: 6 }}>
          {call.title}
        </h3>

        {/* Description */}
        <p style={{ fontSize: 12, color: "#64748b", lineHeight: 1.55, margin: 0, marginBottom: 8 }}>
          {call.description?.slice(0, 180)}{call.description?.length > 180 ? "..." : ""}
        </p>

        {/* Relevance note */}
        {call.relevance_note && (
          <p style={{ fontSize: 11, color: "#15803d", margin: 0, marginBottom: 6, fontStyle: "italic", lineHeight: 1.4 }}>
            💡 {call.relevance_note}
          </p>
        )}

        {/* Bottom row */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#64748b" }}>
            {call.deadline && <span>📅 {call.deadline}</span>}
            {call.budget && <span style={{ color: "#92400e" }}>💰 {call.budget}</span>}
          </div>
          <a href={call.url} target="_blank" rel="noopener noreferrer" style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "5px 14px", borderRadius: 8,
            background: src.color, color: "#fff",
            fontSize: 12, fontWeight: 700, textDecoration: "none",
            transition: "opacity 0.15s",
          }}
            onMouseEnter={e => e.currentTarget.style.opacity = 0.85}
            onMouseLeave={e => e.currentTarget.style.opacity = 1}
          >
            Ver convocatoria →
          </a>
        </div>
      </div>
    </div>
  );
}

// ─── Tab pill component ───
function TabPill({ active, onClick, children, color, count }) {
  return (
    <button onClick={onClick} style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "8px 18px", borderRadius: 99, border: "none",
      background: active ? color : "#f1f5f9",
      color: active ? "#fff" : "#475569",
      fontSize: 13, fontWeight: 700, cursor: "pointer",
      transition: "all 0.2s", whiteSpace: "nowrap",
    }}>
      {children}
      {count !== undefined && (
        <span style={{
          background: active ? "rgba(255,255,255,0.3)" : "#e2e8f0",
          padding: "1px 8px", borderRadius: 99, fontSize: 11, fontWeight: 800,
          minWidth: 22, textAlign: "center",
        }}>{count}</span>
      )}
    </button>
  );
}

// ─── Filter chip ───
function FilterChip({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: "5px 14px", borderRadius: 8,
      border: active ? "2px solid #334155" : "1.5px solid #d1d5db",
      background: active ? "#1e293b" : "#fff",
      color: active ? "#fff" : "#475569",
      fontSize: 12, fontWeight: 600, cursor: "pointer",
      transition: "all 0.15s",
    }}>{children}</button>
  );
}

// ─── Stat card ───
function StatCard({ label, value, color, icon }) {
  return (
    <div style={{
      flex: "1 1 0", minWidth: 100, padding: "14px 16px",
      background: "#fff", borderRadius: 12,
      border: "1px solid #e5e7eb",
    }}>
      <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 2 }}>
        {icon} {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 900, color: color || "#1e293b", letterSpacing: "-0.02em" }}>
        {value}
      </div>
    </div>
  );
}

// ─── Resources panel ───
function ResourcesPanel() {
  const sections = [
    { title: "Europa", icon: "🇪🇺", color: "#1d4ed8", bg: "#eff6ff", border: "#bfdbfe", links: [
      { name: "Portal EU Funding & Tenders", url: "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals" },
      { name: "NetZeroCities (Mission)", url: "https://netzerocities.eu" },
      { name: "URBACT", url: "https://urbact.eu/calls-for-proposals" },
      { name: "INTERREG SUDOE", url: "https://interreg-sudoe.eu" },
      { name: "INTERREG Atlantic", url: "https://www.atlanticarea.eu" },
      { name: "LIFE (CINEA)", url: "https://cinea.ec.europa.eu/programmes/life_en" },
      { name: "EIT Climate-KIC", url: "https://www.climate-kic.org/programmes/" },
      { name: "EIT Urban Mobility", url: "https://www.eiturbanmobility.eu/calls/" },
      { name: "New European Bauhaus", url: "https://new-european-bauhaus.europa.eu/get-involved/funding-opportunities_en" },
      { name: "EUI Innovative Actions", url: "https://www.urban-initiative.eu/calls-for-proposals" },
      { name: "BEI ELENA", url: "https://www.eib.org/en/products/advising/elena/index.htm" },
      { name: "TED Licitaciones", url: "https://ted.europa.eu/en/advanced-search" },
    ]},
    { title: "España", icon: "🇪🇸", color: "#b45309", bg: "#fffbeb", border: "#fde68a", links: [
      { name: "IDAE Ayudas", url: "https://ayudasenergiaidae.es/programas-ayudas-abiertas/" },
      { name: "CDTI Convocatorias", url: "https://www.cdti.es/convocatorias" },
      { name: "Fundación Biodiversidad", url: "https://fundacion-biodiversidad.es/convocatorias/" },
      { name: "MITECO", url: "https://www.miteco.gob.es/es/ministerio/servicios/ayudas-subvenciones/" },
      { name: "BDNS", url: "https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias" },
      { name: "FEMP Fondos Europeos", url: "https://femp-fondos-europa.es/convocatorias/" },
      { name: "Red Innpulso", url: "https://www.redinnpulso.es/" },
    ]},
    { title: "Euskadi / Bizkaia", icon: "🏔️", color: "#047857", bg: "#ecfdf5", border: "#6ee7b7", links: [
      { name: "EVE Ayudas", url: "https://www.eve.eus/programa-de-ayudas/" },
      { name: "Ihobe Subvenciones", url: "https://www.ihobe.eus/subvenciones" },
      { name: "SPRI Programas", url: "https://www.spri.eus/es/ayudas/" },
      { name: "Diputación Bizkaia", url: "https://www.bizkaia.eus/es/subvenciones" },
      { name: "Gobierno Vasco", url: "https://www.euskadi.eus/ayudas-subvenciones-702/web01-tramite/es/" },
      { name: "Udalsarea 2030", url: "https://www.udalsarea21.net/" },
      { name: "Barrixe", url: "https://barrixe.com/" },
      { name: "KontratazioA", url: "https://www.contratacion.euskadi.eus" },
    ]},
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
      {sections.map(s => (
        <div key={s.title} style={{
          background: s.bg, border: `1px solid ${s.border}`,
          borderRadius: 12, padding: "14px 18px",
        }}>
          <div style={{ fontWeight: 800, fontSize: 13, color: s.color, marginBottom: 8 }}>
            {s.icon} {s.title}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 16px" }}>
            {s.links.map(l => (
              <a key={l.name} href={l.url} target="_blank" rel="noopener noreferrer" style={{
                color: s.color, fontSize: 12, fontWeight: 600, textDecoration: "none",
                lineHeight: 2,
              }}
                onMouseEnter={e => e.currentTarget.style.textDecoration = "underline"}
                onMouseLeave={e => e.currentTarget.style.textDecoration = "none"}
              >{l.name}</a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── MAIN DASHBOARD ───
export default function FundingRadar() {
  const [data] = useState(SAMPLE_DATA);
  const [activeTab, setActiveTab] = useState("all"); // all | EU | BDNS | KontratazioA
  const [relevanceFilter, setRelevanceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [programmeFilter, setProgrammeFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const [showResources, setShowResources] = useState(false);
  const [sortBy, setSortBy] = useState("relevance"); // relevance | deadline | newest

  const newCallIds = useMemo(() => new Set(data.slice(0, 5).map(d => d.id)), [data]);

  const counts = useMemo(() => {
    const eu = data.filter(c => getSourceKey(c) === "EU").length;
    const es = data.filter(c => getSourceKey(c) === "BDNS").length;
    const eus = data.filter(c => getSourceKey(c) === "KontratazioA").length;
    const muyAlta = data.filter(c => c.relevance_level === "MUY ALTA").length;
    const abiertas = data.filter(c => c.status === "Open").length;
    return { total: data.length, eu, es, eus, muyAlta, abiertas, new: newCallIds.size };
  }, [data, newCallIds]);

  const filtered = useMemo(() => {
    let result = [...data];

    // Tab filter
    if (activeTab !== "all") {
      result = result.filter(c => getSourceKey(c) === activeTab);
    }

    // Relevance
    if (relevanceFilter !== "all") {
      result = result.filter(c => c.relevance_level === relevanceFilter);
    }

    // Status
    if (statusFilter !== "all") {
      if (statusFilter === "new") {
        result = result.filter(c => newCallIds.has(c.id));
      } else {
        result = result.filter(c => c.status === statusFilter);
      }
    }

    // Programme
    if (programmeFilter !== "all") {
      result = result.filter(c => c.programme === programmeFilter);
    }

    // Search
    if (searchText.trim()) {
      const q = searchText.toLowerCase();
      result = result.filter(c =>
        c.title.toLowerCase().includes(q) ||
        c.description?.toLowerCase().includes(q) ||
        c.programme?.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q)
      );
    }

    // Sort
    const relOrder = { "MUY ALTA": 0, "ALTA": 1, "MEDIA": 2, "INFO": 3 };
    if (sortBy === "relevance") {
      result.sort((a, b) => (relOrder[a.relevance_level] ?? 9) - (relOrder[b.relevance_level] ?? 9));
    } else if (sortBy === "deadline") {
      result.sort((a, b) => {
        const da = daysUntilDeadline(a.deadline);
        const db = daysUntilDeadline(b.deadline);
        if (da === null && db === null) return 0;
        if (da === null) return 1;
        if (db === null) return -1;
        return da - db;
      });
    }

    return result;
  }, [data, activeTab, relevanceFilter, statusFilter, programmeFilter, searchText, sortBy, newCallIds]);

  const activeProgrammes = useMemo(() => {
    const progs = new Set();
    data.forEach(c => { if (c.programme) progs.add(c.programme); });
    return Array.from(progs).sort();
  }, [data]);

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%)",
      fontFamily: "'DM Sans', 'Segoe UI', -apple-system, sans-serif",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

      {/* ─── HEADER ─── */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)",
        padding: "24px 24px 20px",
        color: "#fff",
      }}>
        <div style={{ maxWidth: 960, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12,
              background: "linear-gradient(135deg, #fbbf24, #f59e0b)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 22, fontWeight: 900,
            }}>⚡</div>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>
                Funding Radar
              </h1>
              <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 1 }}>
                Bilbao · Misión Climática · Neutralidad 2030
              </div>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              <button onClick={() => setShowResources(!showResources)} style={{
                padding: "7px 16px", borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.2)",
                background: showResources ? "rgba(255,255,255,0.15)" : "transparent",
                color: "#e2e8f0", fontSize: 12, fontWeight: 700, cursor: "pointer",
              }}>🔗 Recursos</button>
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <StatCard icon="📊" label="Total" value={counts.total} />
            <StatCard icon="🆕" label="Nuevas" value={counts.new} color="#dc2626" />
            <StatCard icon="🇪🇺" label="Europa" value={counts.eu} color="#1d4ed8" />
            <StatCard icon="🇪🇸" label="España" value={counts.es} color="#b45309" />
            <StatCard icon="🏔️" label="Euskadi" value={counts.eus} color="#047857" />
            <StatCard icon="🟢" label="Muy Alta" value={counts.muyAlta} color="#15803d" />
          </div>
        </div>
      </div>

      {/* ─── BODY ─── */}
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "20px 24px 40px" }}>

        {/* Source tabs — the KEY visual differentiator */}
        <div style={{
          display: "flex", gap: 8, marginBottom: 16,
          padding: "6px", background: "#fff", borderRadius: 99,
          border: "1px solid #e5e7eb",
          flexWrap: "wrap",
        }}>
          <TabPill active={activeTab === "all"} onClick={() => setActiveTab("all")} color="#1e293b" count={counts.total}>
            Todas
          </TabPill>
          <TabPill active={activeTab === "EU"} onClick={() => setActiveTab("EU")} color="#1d4ed8" count={counts.eu}>
            🇪🇺 Europa
          </TabPill>
          <TabPill active={activeTab === "BDNS"} onClick={() => setActiveTab("BDNS")} color="#b45309" count={counts.es}>
            🇪🇸 España
          </TabPill>
          <TabPill active={activeTab === "KontratazioA"} onClick={() => setActiveTab("KontratazioA")} color="#047857" count={counts.eus}>
            🏔️ Euskadi
          </TabPill>
        </div>

        {/* Search + filters row */}
        <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ flex: "1 1 220px", position: "relative" }}>
            <input
              type="text"
              placeholder="Buscar convocatorias..."
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              style={{
                width: "100%", padding: "9px 14px 9px 36px",
                borderRadius: 10, border: "1.5px solid #d1d5db",
                fontSize: 13, outline: "none", background: "#fff",
                boxSizing: "border-box",
              }}
              onFocus={e => e.target.style.borderColor = "#3b82f6"}
              onBlur={e => e.target.style.borderColor = "#d1d5db"}
            />
            <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontSize: 14, color: "#94a3b8" }}>🔍</span>
          </div>

          <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
            padding: "9px 14px", borderRadius: 10, border: "1.5px solid #d1d5db",
            fontSize: 12, fontWeight: 600, color: "#475569", background: "#fff", cursor: "pointer",
          }}>
            <option value="relevance">↕ Relevancia</option>
            <option value="deadline">↕ Deadline</option>
          </select>
        </div>

        {/* Filter chips row */}
        <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase", marginRight: 4 }}>Relevancia:</span>
          {["all", "MUY ALTA", "ALTA", "MEDIA"].map(r => (
            <FilterChip key={r} active={relevanceFilter === r} onClick={() => setRelevanceFilter(r)}>
              {r === "all" ? "Todas" : REL_CONFIG[r]?.dot + " " + REL_CONFIG[r]?.label}
            </FilterChip>
          ))}
        </div>
        <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase", marginRight: 4 }}>Estado:</span>
          <FilterChip active={statusFilter === "all"} onClick={() => setStatusFilter("all")}>Todas</FilterChip>
          <FilterChip active={statusFilter === "new"} onClick={() => setStatusFilter("new")}>🆕 Nuevas</FilterChip>
          <FilterChip active={statusFilter === "Open"} onClick={() => setStatusFilter("Open")}>Abiertas</FilterChip>
          <FilterChip active={statusFilter === "Forthcoming"} onClick={() => setStatusFilter("Forthcoming")}>Próximas</FilterChip>
        </div>
        <div style={{ display: "flex", gap: 6, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase", marginRight: 4 }}>Programa:</span>
          <FilterChip active={programmeFilter === "all"} onClick={() => setProgrammeFilter("all")}>Todos</FilterChip>
          {activeProgrammes.map(p => (
            <FilterChip key={p} active={programmeFilter === p} onClick={() => setProgrammeFilter(p)}>
              {p}
            </FilterChip>
          ))}
        </div>

        {/* Resources panel (collapsible) */}
        {showResources && <ResourcesPanel />}

        {/* Active filters summary */}
        {(activeTab !== "all" || relevanceFilter !== "all" || statusFilter !== "all" || programmeFilter !== "all" || searchText) && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginBottom: 12,
            padding: "8px 14px", background: "#f1f5f9", borderRadius: 10,
            fontSize: 12, color: "#64748b",
          }}>
            <span style={{ fontWeight: 700 }}>{filtered.length}</span> resultado{filtered.length !== 1 ? "s" : ""}
            <button onClick={() => {
              setActiveTab("all"); setRelevanceFilter("all"); setStatusFilter("all");
              setProgrammeFilter("all"); setSearchText("");
            }} style={{
              marginLeft: "auto", padding: "3px 10px", borderRadius: 6,
              border: "1px solid #cbd5e1", background: "#fff",
              fontSize: 11, fontWeight: 600, cursor: "pointer", color: "#64748b",
            }}>✕ Limpiar filtros</button>
          </div>
        )}

        {/* ─── CARDS LIST ─── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filtered.length === 0 && (
            <div style={{
              textAlign: "center", padding: 40, color: "#94a3b8",
              background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb",
            }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
              <div style={{ fontWeight: 600 }}>Sin resultados con estos filtros</div>
              <div style={{ fontSize: 13, marginTop: 4 }}>Prueba a cambiar los filtros o ampliar la búsqueda</div>
            </div>
          )}
          {filtered.map(call => (
            <CallCard key={call.id} call={call} isNew={newCallIds.has(call.id)} />
          ))}
        </div>

        {/* Footer */}
        <div style={{
          textAlign: "center", marginTop: 32, padding: "16px 0",
          fontSize: 11, color: "#94a3b8", borderTop: "1px solid #e5e7eb",
        }}>
          Funding Radar · Ayto. Bilbao · Fuentes: API SEDIA (EU) + BDNS (España) + euskadi.eus (Euskadi)
        </div>
      </div>
    </div>
  );
}
