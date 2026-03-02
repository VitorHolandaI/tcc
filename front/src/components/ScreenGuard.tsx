import React, { useEffect, useState, useCallback } from "react";

interface ScreenGuardProps {
  children: React.ReactNode;
}

/**
 * ScreenGuard: Ensures user is in fullscreen mode before showing the exam.
 *
 * Note: Screen share + recording is handled by TextBox component.
 * This guard only enforces fullscreen to prevent the user from accessing other apps/tabs.
 */
const ScreenGuard = ({ children }: ScreenGuardProps) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFullscreenChange = useCallback(() => {
    const isFs = !!document.fullscreenElement;
    setIsFullscreen(isFs);
  }, []);

  useEffect(() => {
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, [handleFullscreenChange]);

  const handleEnterFullscreen = async () => {
    try {
      await document.documentElement.requestFullscreen();
    } catch (err) {
      setError("Não foi possível entrar em tela cheia. Tente pressionar F11.");
    }
  };

  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      {!isFullscreen ? (
        <div style={overlayStyle}>
          <h2 style={{ marginBottom: "0.5rem" }}>Preparação para a Prova</h2>
          <p style={{ color: "#64748b", marginBottom: "2rem" }}>
            Entre em modo tela cheia para iniciar a prova.
          </p>

          {error && <p style={errorStyle}>{error}</p>}

          <div style={stepStyle(isFullscreen)}>
            <div style={stepNumberStyle(isFullscreen)}>1</div>
            <div style={{ textAlign: "left", flex: 1 }}>
              <strong>Tela cheia</strong>
              <p style={{ fontSize: "0.85rem", color: "#64748b", margin: "0.25rem 0 0" }}>
                Entre em modo tela cheia (F11). A gravação de tela, webcam e áudio será solicitada após este passo.
              </p>
            </div>
            {!isFullscreen ? (
              <button onClick={handleEnterFullscreen} style={buttonStyle}>
                Tela Cheia (F11)
              </button>
            ) : (
              <span style={checkStyle}> OK</span>
            )}
          </div>
        </div>
      ) : (
        <div className="protected-content">
          {children}
        </div>
      )}
    </div>
  );
};

const overlayStyle: React.CSSProperties = {
  minHeight: "60vh",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  border: "2px solid #e2e8f0",
  borderRadius: "16px",
  backgroundColor: "#fff",
  padding: "3rem 2rem",
  maxWidth: "560px",
  margin: "0 auto",
};

const stepStyle = (done: boolean): React.CSSProperties => ({
  display: "flex",
  alignItems: "center",
  gap: "1rem",
  width: "100%",
  padding: "1rem 1.25rem",
  borderRadius: "12px",
  border: `1px solid ${done ? "#bbf7d0" : "#e2e8f0"}`,
  backgroundColor: done ? "#f0fdf4" : "#fafafa",
  marginBottom: "0.75rem",
});

const stepNumberStyle = (done: boolean): React.CSSProperties => ({
  width: "32px",
  height: "32px",
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 700,
  fontSize: "0.85rem",
  backgroundColor: done ? "#16a34a" : "#e2e8f0",
  color: done ? "#fff" : "#64748b",
  flexShrink: 0,
});

const buttonStyle: React.CSSProperties = {
  padding: "0.6rem 1.25rem",
  cursor: "pointer",
  fontSize: "0.85rem",
  fontWeight: 600,
  border: "none",
  borderRadius: "8px",
  backgroundColor: "#2563eb",
  color: "#fff",
  flexShrink: 0,
};

const checkStyle: React.CSSProperties = {
  color: "#16a34a",
  fontWeight: 700,
  fontSize: "0.9rem",
  flexShrink: 0,
};

const errorStyle: React.CSSProperties = {
  color: "#dc2626",
  fontWeight: 600,
  backgroundColor: "#fef2f2",
  padding: "0.75rem 1rem",
  borderRadius: "8px",
  marginBottom: "1rem",
  width: "100%",
  fontSize: "0.85rem",
};

export default ScreenGuard;
