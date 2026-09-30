import { NavLink, Outlet } from "react-router-dom";
import "./DashboardLayout.css";

function DashboardLayout() {
  return (
    <div className="app-layout">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">✚</div>

          <div>
            <h2>CareBridge</h2>
            <span>AI Healthcare Assistant</span>
          </div>
        </div>

        <nav className="sidebar-nav">

          <NavLink to="/" className="nav-item">
            <span>⌂</span>
            Dashboard
          </NavLink>

          <NavLink to="/upload" className="nav-item">
            <span>↑</span>
            Upload Summary
          </NavLink>

          <NavLink to="/summary" className="nav-item">
            <span>▤</span>
            Summary
          </NavLink>

          <NavLink to="/medications" className="nav-item">
            <span>▣</span>
            Medications
          </NavLink>

          <NavLink to="/follow-up" className="nav-item">
            <span>◷</span>
            Follow-up
          </NavLink>

          <NavLink to="/instructions" className="nav-item">
            <span>☑</span>
            Instructions
          </NavLink>

          <NavLink to="/important-info" className="nav-item">
            <span>⚠</span>
            Important Info
          </NavLink>

          <NavLink to="/ask-ai" className="nav-item">
            <span>✦</span>
            Ask AI
          </NavLink>

          <NavLink to="/history" className="nav-item">
            <span>◫</span>
            History
          </NavLink>

        </nav>

        <div className="sidebar-footer">
          <div className="safety-note">
            <strong>AI Assistance</strong>
            <p>
              Information is extracted from the
              uploaded discharge summary.
            </p>
          </div>
        </div>

      </aside>

      {/* Main section */}
      <div className="main-section">

        <header className="top-header">

          <div>
            <h1>Discharge Summary Explainer</h1>
            <p>
              Understand discharge information clearly and quickly.
            </p>
          </div>

          <div className="header-actions">

            <button className="language-button">
              🌐 English ▾
            </button>

            <div className="user-profile">
              <div className="user-avatar">
                N
              </div>

              <div>
                <strong>Nurse</strong>
                <span>Healthcare Worker</span>
              </div>
            </div>

          </div>

        </header>

        <main className="page-content">
          <Outlet />
        </main>

      </div>

    </div>
  );
}

export default DashboardLayout;