// ProtectedPage.tsx
import ScreenGuard from "./ScreenGuard";

const ProtectedPage = () => {
  return (
    <ScreenGuard>
      {/* Everything inside here is hidden until recording starts */}
      <div style={{ padding: "20px" }}>
        <h1>Page</h1>
        <p>Visible because you are recording.</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        </div>
      </div>
    </ScreenGuard>
  );
};

	//const cardStyle = { padding: '20px', background: '#e0e0e0', borderRadius: '8px' };

export default ProtectedPage;
