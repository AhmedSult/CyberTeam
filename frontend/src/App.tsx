import { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import {
  api,
  type ComplianceRecord,
  type Control,
  type CurrentUser,
  type DashboardStats,
  type Department,
  type Framework,
  getToken,
  setToken,
} from "./api";
import { AppShell } from "./components/AppShell";
import { Spinner } from "./components/Spinner";
import { AssistantPage } from "./pages/AssistantPage";
import { HomePage } from "./pages/HomePage";

function TrustBar() {
  return (
    <div className="nca-trust-bar" dir="rtl">
      المواقع الإلكترونية الحكومية الرسمية تنتهي بـ <strong>.gov.sa</strong> وتستخدم{" "}
      <strong>HTTPS</strong> للتشفير والأمان — للاطلاع على السياسات والضوابط الرسمية:{" "}
      <a href="https://nca.gov.sa/ar/" target="_blank" rel="noopener noreferrer">
        الهيئة الوطنية للأمن السيبراني (NCA)
      </a>
    </div>
  );
}

function AppFooter() {
  return (
    <footer className="nca-footer" dir="rtl">
      <strong>تنويه:</strong> هذه المنصة مشروع/بيئة عرض أو داخلية و<strong>ليست</strong> تابعة للهيئة
      الوطنية للأمن السيبراني. المرجع الرسمي للوثائق والخدمات:{" "}
      <a href="https://nca.gov.sa/ar/" target="_blank" rel="noopener noreferrer">
        nca.gov.sa
      </a>
    </footer>
  );
}

function LoginView({
  email,
  setEmail,
  password,
  setPassword,
  err,
  onLogin,
  loginLoading,
}: {
  email: string;
  setEmail: (v: string) => void;
  password: string;
  setPassword: (v: string) => void;
  err: string | null;
  onLogin: (e: React.FormEvent) => void;
  loginLoading: boolean;
}) {
  return (
    <>
      <TrustBar />
      <div style={loginStyles.shell}>
        <div style={{ maxWidth: 480, width: "100%" }}>
          <p style={loginStyles.loginLead}>فضاء سيبراني أكثر جاهزية وموثوقية</p>
          <p style={loginStyles.loginSub}>
            إدارة الضوابط والامتثال بشكل مركزي — مع إرشادات تطبيق ومساعد ذكاء اصطناعي للتحليل
          </p>
          <div style={loginStyles.card}>
            <h1 style={loginStyles.h1}>تسجيل الدخول</h1>
            <p style={loginStyles.muted}>تجريبي: admin@example.com / admin123</p>
            <form onSubmit={onLogin} style={loginStyles.form}>
              <label style={loginStyles.label}>
                البريد الإلكتروني
                <input style={loginStyles.input} value={email} onChange={(e) => setEmail(e.target.value)} />
              </label>
              <label style={loginStyles.label}>
                كلمة المرور
                <input
                  type="password"
                  style={loginStyles.input}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {err && <p style={{ color: "var(--danger)", margin: 0, fontSize: "0.9rem" }}>{err}</p>}
              <button
                type="submit"
                style={{
                  ...loginStyles.btnPrimary,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.45rem",
                  opacity: loginLoading ? 0.85 : 1,
                  cursor: loginLoading ? "wait" : "pointer",
                }}
                disabled={loginLoading}
                aria-busy={loginLoading}
              >
                {loginLoading && <Spinner tone="inverse" />}
                {loginLoading ? "جاري الدخول…" : "دخول آمن"}
              </button>
            </form>
          </div>
        </div>
      </div>
      <AppFooter />
    </>
  );
}

export default function App() {
  const [token, setTok] = useState<string | null>(() => getToken());
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [err, setErr] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [controls, setControls] = useState<Control[]>([]);
  const [records, setRecords] = useState<ComplianceRecord[]>([]);
  const [depts, setDepts] = useState<Department[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [fw, setFw] = useState<number | "">("");
  const [deptFilter, setDeptFilter] = useState<number | "">("");
  const [chat, setChat] = useState("");
  const [chatLog, setChatLog] = useState<{ role: "user" | "ai"; text: string }[]>([]);
  const [gap, setGap] = useState<string | null>(null);
  const [gapLoading, setGapLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [patchingRecordId, setPatchingRecordId] = useState<number | null>(null);
  const [chatSending, setChatSending] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const u = await api.me();
        if (!cancelled && u) setCurrentUser(u);
      } catch {
        if (!cancelled) setCurrentUser(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [s, c, r, d, f] = await Promise.all([
        api.stats(),
        api.controls(typeof fw === "number" ? fw : undefined),
        api.records(typeof deptFilter === "number" ? deptFilter : undefined),
        api.departments(),
        api.frameworks(),
      ]);
      setStats(s);
      setControls(c);
      setRecords(r);
      setDepts(d);
      setFrameworks(f);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "خطأ");
    } finally {
      setLoading(false);
    }
  }, [fw, deptFilter]);

  useEffect(() => {
    if (token) void loadData();
  }, [token, loadData]);

  /* تحليل الفجوات يعتمد على فلتر الإدارة/الإطار وتصفية الجدول — إعادة التعيين عند تغيير الإدارة/الإطار */
  useEffect(() => {
    setGap(null);
  }, [fw, deptFilter]);

  const clearGapSummary = useCallback(() => setGap(null), []);

  const controlById = useMemo(() => {
    const m = new Map<number, Control>();
    controls.forEach((c) => m.set(c.id, c));
    return m;
  }, [controls]);

  const deptById = useMemo(() => {
    const m = new Map<number, Department>();
    depts.forEach((d) => m.set(d.id, d));
    return m;
  }, [depts]);

  async function onLogin(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoginLoading(true);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      setTok(access_token);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "فشل الدخول");
    } finally {
      setLoginLoading(false);
    }
  }

  function logout() {
    setToken(null);
    setTok(null);
  }

  async function sendChat() {
    if (!chat.trim() || chatSending) return;
    const u = chat.trim();
    setChat("");
    setChatLog((l) => [...l, { role: "user", text: u }]);
    setChatSending(true);
    try {
      const r = await api.aiChat(u, {
        department_id: typeof deptFilter === "number" ? deptFilter : undefined,
        framework_id: typeof fw === "number" ? fw : undefined,
        gap_summary: gap ?? undefined,
        include_compliance_snapshot: true,
      });
      setChatLog((l) => [...l, { role: "ai", text: r.reply + (r.used_llm ? "" : " ") }]);
    } catch (e) {
      setChatLog((l) => [...l, { role: "ai", text: String(e) }]);
    } finally {
      setChatSending(false);
    }
  }

  async function runGap(opts?: { control_ids?: number[] }) {
    if (gapLoading) return;
    setGap(null);
    setGapLoading(true);
    try {
      const r = await api.gapAnalysis({
        department_id: typeof deptFilter === "number" ? deptFilter : undefined,
        framework_id: typeof fw === "number" ? fw : undefined,
        control_ids: opts?.control_ids,
      });
      setGap(r.gaps_summary + (r.used_llm ? " (نموذج لغوي)" : " (تحليل قاعدي)"));
    } catch (e) {
      setGap(String(e));
    } finally {
      setGapLoading(false);
    }
  }

  async function updateStatus(rec: ComplianceRecord, status: ComplianceRecord["status"]) {
    setPatchingRecordId(rec.id);
    try {
      await api.patchRecord(rec.id, { status });
      await loadData();
    } catch (e) {
      setErr(String(e));
    } finally {
      setPatchingRecordId(null);
    }
  }

  if (!token) {
    return (
      <LoginView
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        err={err}
        onLogin={onLogin}
        loginLoading={loginLoading}
      />
    );
  }

  return (
    <BrowserRouter>
      <TrustBar />
      <Routes>
        <Route element={<AppShell onLogout={logout} />}>
          <Route
            index
            element={
              <HomePage
                err={err}
                stats={stats}
                frameworks={frameworks}
                fw={fw}
                setFw={setFw}
                depts={depts}
                deptFilter={deptFilter}
                setDeptFilter={setDeptFilter}
                loading={loading}
                loadData={loadData}
                gapLoading={gapLoading}
                gap={gap}
                runGap={runGap}
                onComplianceTableFilterChange={clearGapSummary}
                currentUser={currentUser}
                records={records}
                controlById={controlById}
                deptById={deptById}
                patchingRecordId={patchingRecordId}
                updateStatus={updateStatus}
                chat={chat}
                setChat={setChat}
                chatLog={chatLog}
                sendChat={sendChat}
                chatSending={chatSending}
              />
            }
          />
          <Route
            path="assistant"
            element={
              <AssistantPage
                chat={chat}
                setChat={setChat}
                chatLog={chatLog}
                sendChat={sendChat}
                chatSending={chatSending}
              />
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <AppFooter />
    </BrowserRouter>
  );
}

const loginStyles: Record<string, React.CSSProperties> = {
  shell: {
    minHeight: "calc(100vh - 120px)",
    display: "grid",
    placeItems: "center",
    padding: "2rem 1.25rem",
  },
  loginLead: {
    fontFamily: "Tajawal, var(--font-body)",
    fontWeight: 800,
    fontSize: "1.5rem",
    color: "var(--nca-green-dark)",
    margin: "0 0 0.5rem",
    lineHeight: 1.3,
    textAlign: "center",
  },
  loginSub: {
    color: "var(--muted)",
    fontSize: "0.95rem",
    margin: "0 0 1.5rem",
    textAlign: "center",
    lineHeight: 1.65,
    maxWidth: 420,
    marginLeft: "auto",
    marginRight: "auto",
  },
  card: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 16,
    padding: "1.75rem",
    width: "100%",
    boxShadow: "var(--shadow-md)",
    borderTop: "4px solid var(--nca-green)",
  },
  h1: {
    marginTop: 0,
    fontFamily: "Tajawal, var(--font-body)",
    fontWeight: 800,
    color: "var(--nca-green-dark)",
    fontSize: "1.35rem",
  },
  muted: { color: "var(--muted)", fontSize: "0.9rem" },
  form: { display: "flex", flexDirection: "column", gap: 12 },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem", fontWeight: 600 },
  input: {
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid var(--border)",
    background: "var(--surface)",
    color: "var(--text)",
    boxShadow: "var(--shadow-sm)",
  },
  btnPrimary: {
    padding: "12px 16px",
    borderRadius: 10,
    border: "none",
    background: "linear-gradient(165deg, var(--nca-green) 0%, var(--accent-dim) 100%)",
    color: "#fff",
    fontWeight: 700,
    cursor: "pointer",
    fontFamily: "Tajawal, var(--font-body)",
    boxShadow: "0 4px 14px rgba(0, 107, 63, 0.25)",
  },
};
