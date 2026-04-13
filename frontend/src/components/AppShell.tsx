import { NavLink, Outlet } from "react-router-dom";

function AssistantIcon() {
  return (
    <svg className="nav-ai-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
      />
    </svg>
  );
}

function HomeIcon() {
  return (
    <svg className="nav-home-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M3 10.5L12 3l9 7.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-9.5z" strokeLinejoin="round" />
    </svg>
  );
}

export function AppShell({ onLogout }: { onLogout: () => void }) {
  return (
    <>
      <header className="app-topnav" dir="rtl">
        <div className="app-topnav-inner">
          <div className="app-topnav-brand">
            <span className="app-topnav-title">لوحة الامتثال والضوابط السيبرانية</span>
            <span className="app-topnav-sub">تتبع الجاهزية والامتثال — مع مساعد ذكي</span>
          </div>
          <nav className="app-topnav-actions" aria-label="التنقل الرئيسي">
            <NavLink
              to="/"
              end
              className={({ isActive }) => (isActive ? "nav-pill nav-pill--active" : "nav-pill")}
            >
              <HomeIcon />
              الصفحة الرئيسية
            </NavLink>
            <NavLink
              to="/assistant"
              className={({ isActive }) => (isActive ? "nav-ai nav-ai--active" : "nav-ai")}
              title="فتح مساعد الامتثال الذكي"
            >
              <AssistantIcon />
              <span className="nav-ai-label">المساعد الذكي</span>
            </NavLink>
            <button type="button" className="nav-logout" onClick={onLogout}>
              تسجيل الخروج
            </button>
          </nav>
        </div>
      </header>
      <Outlet />
    </>
  );
}
