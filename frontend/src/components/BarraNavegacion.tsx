import { Shield, LogOut } from "lucide-react";
import { Alerta, UsuarioLogin } from "../tipos";

interface Props {
    tab:           string;
    setTab:        (tab: string) => void;
    alertas:       Alerta[];
    conectado:     boolean;
    esAdmin:       boolean;
    usuarioActual: UsuarioLogin;
    onLogout:      () => void;
}

const BarraNavegacion = ({ tab, setTab, alertas, conectado, esAdmin, usuarioActual, onLogout }: Props) => {
    const tabs = [
        { key: "paciente",  label: "Paciente" },
        { key: "overview",  label: "Monitor" },
        { key: "analytics", label: "Analytics" },
        { key: "alertas",   label: "Alertas" },
        { key: "config",    label: "Configuración" },
        ...(esAdmin ? [{ key: "admin", label: "Administración" }] : []),
    ];

    return (
        <header style={{
            position: "sticky", top: 0, zIndex: 100,
            background: "rgba(7,11,20,0.92)", backdropFilter: "blur(20px)",
            borderBottom: "1px solid rgba(0,229,255,0.1)",
            padding: "0 32px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            height: 64,
        }}>
            {/* Logo */}
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{
                    width: 36, height: 36, borderRadius: 10,
                    background: "linear-gradient(135deg, #ef4444, #f43f5e)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: "0 0 20px #ef444460",
                }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                        <path d="M12 21.593c-5.63-5.539-11-10.297-11-14.402C1 3.518 3.318 1 6.5 1c1.863 0 3.404 1.109 4.5 2.695C12.096 2.109 13.637 1 15.5 1 18.682 1 21 3.518 21 7.191c0 4.105-5.37 8.863-11 14.402z" />
                    </svg>
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.3px", color: "#f1f5f9" }}>
                    Sistema de Monitoreo - Posta Médica
                </div>
            </div>

            {/* Tabs */}
            <nav style={{ display: "flex", gap: 4 }}>
                {tabs.map(({ key, label }) => (
                    <button key={key} onClick={() => setTab(key)} style={{
                        background: tab === key ? "rgba(0,229,255,0.12)" : "transparent",
                        border: tab === key ? "1px solid rgba(0,229,255,0.3)" : "1px solid transparent",
                        color: tab === key
                            ? "#00e5ff"
                            : key === "admin" ? "rgba(167,139,250,0.7)" : "#6b7280",
                        borderRadius: 8, padding: "6px 16px",
                        fontSize: 12, fontWeight: 600, cursor: "pointer",
                        letterSpacing: "0.03em", transition: "all 0.2s",
                        display: "flex", alignItems: "center", gap: 6,
                    }}>
                        {key === "admin" && <Shield size={12}/>}
                        {label}
                        {key === "alertas" && alertas.length > 0 && (
                            <span style={{
                                background: "#ef4444", color: "white",
                                borderRadius: 99, padding: "1px 6px", fontSize: 10,
                            }}>{alertas.length}</span>
                        )}
                    </button>
                ))}
            </nav>

            {/* Derecha: conexión + usuario + logout */}
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                        width: 8, height: 8, borderRadius: "50%",
                        background: conectado ? "#10b981" : "#ef4444",
                        boxShadow: conectado ? "0 0 8px #10b981" : "0 0 8px #ef4444",
                        animation: conectado ? "pulse 2s infinite" : "none",
                    }} />
                    <span style={{ fontSize: 11, color: "#6b7280", fontFamily: "'JetBrains Mono', monospace" }}>
                        {conectado ? "EN VIVO" : "DESCONECTADO"}
                    </span>
                </div>

                {/* Usuario actual */}
                <div style={{
                    fontSize: 11, fontFamily: "'JetBrains Mono', monospace",
                    color: esAdmin ? "#a78bfa" : "#6b7280",
                    background: esAdmin ? "rgba(167,139,250,0.08)" : "rgba(255,255,255,0.04)",
                    border: `1px solid ${esAdmin ? "rgba(167,139,250,0.2)" : "rgba(255,255,255,0.06)"}`,
                    borderRadius: 6, padding: "3px 10px",
                    display: "flex", alignItems: "center", gap: 5,
                }}>
                    {esAdmin && <Shield size={10}/>}
                    {usuarioActual.nombre || usuarioActual.usuario}
                </div>

                {/* Logout */}
                <button onClick={onLogout} style={{
                    background: "rgba(239,68,68,0.07)",
                    border: "1px solid rgba(239,68,68,0.2)",
                    color: "#ef4444", borderRadius: 7,
                    padding: "5px 12px", fontSize: 11,
                    cursor: "pointer", fontWeight: 600,
                    display: "flex", alignItems: "center", gap: 5,
                    fontFamily: "'JetBrains Mono', monospace",
                }}>
                    <LogOut size={12}/> Salir
                </button>
            </div>
        </header>
    );
};

export default BarraNavegacion;