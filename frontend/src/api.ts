const base = "/api";

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem("token", t);
  else localStorage.removeItem("token");
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const hadStoredToken = !!getToken();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string>),
  };
  const tok = getToken();
  if (tok) headers.Authorization = `Bearer ${tok}`;
  const r = await fetch(`${base}${path}`, { ...init, headers });
  if (!r.ok) {
    /* رمز JWT موقّع بمفتاح قديم أو منتهي — نمسح التخزين ونعيد تحميل صفحة الدخول */
    if (r.status === 401 && hadStoredToken && !path.startsWith("/auth/")) {
      setToken(null);
      window.location.reload();
      return undefined as T;
    }
    const err = await r.text();
    throw new Error(err || r.statusText);
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  stats: () => req<DashboardStats>("/dashboard/stats"),
  frameworks: () => req<Framework[]>("/controls/frameworks"),
  controls: (frameworkId?: number) =>
    req<Control[]>(`/controls${frameworkId != null ? `?framework_id=${frameworkId}` : ""}`),
  records: (departmentId?: number) =>
    req<ComplianceRecord[]>(
      `/compliance/records${departmentId != null ? `?department_id=${departmentId}` : ""}`
    ),
  departments: () => req<Department[]>("/departments"),
  createDepartment: (body: { name_ar: string; name_en: string; code?: string | null }) =>
    req<Department>("/departments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  me: () => req<CurrentUser>("/auth/me"),
  patchRecord: (id: number, body: Partial<Pick<ComplianceRecord, "status" | "evidence_summary">>) =>
    req<ComplianceRecord>(`/compliance/records/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  aiChat: (
    message: string,
    opts?: {
      context_control_id?: number;
      /** يطابق فلتر «الإدارة» في اللوحة — لقطة الامتثال والنسب ضمن هذا النطاق */
      department_id?: number;
      /** يطابق فلتر «الإطار» في اللوحة */
      framework_id?: number;
      /** آخر تحليل فجوات ظاهر في الشريط الجانبي ليربط المساعد به */
      gap_summary?: string | null;
      include_compliance_snapshot?: boolean;
    }
  ) =>
    req<{ reply: string; used_llm: boolean }>("/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        context_control_id: opts?.context_control_id,
        department_id: opts?.department_id,
        framework_id: opts?.framework_id,
        gap_summary: opts?.gap_summary ?? undefined,
        include_compliance_snapshot: opts?.include_compliance_snapshot ?? true,
      }),
    }),
  explainFramework: (framework_id: number) =>
    req<{ explanation: string; used_llm: boolean; official_ecc_pdf_url: string }>(
      "/ai/explain-framework",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ framework_id }),
      }
    ),
  gapAnalysis: (opts?: {
    department_id?: number;
    framework_id?: number;
    /** يطابق الضوابط الظاهرة في جدول الامتثال بعد التصفية والبحث */
    control_ids?: number[];
  }) =>
    req<{ gaps_summary: string; prioritized_controls: number[]; used_llm: boolean }>(
      "/ai/gap-analysis",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          department_id: opts?.department_id,
          framework_id: opts?.framework_id,
          control_ids: opts?.control_ids,
        }),
      }
    ),
};

export type Framework = {
  id: number;
  code: string;
  name_ar: string;
  name_en: string;
  description: string | null;
};

export type Control = {
  id: number;
  framework_id: number;
  control_ref: string;
  title_ar: string;
  title_en: string;
  domain_ar: string | null;
  standard_title_ar: string | null;
  objective_ar: string | null;
  description_ar: string | null;
  implementation_guidance_ar: string | null;
  evidence_guidance_ar: string | null;
  category: string | null;
};

export type ComplianceRecord = {
  id: number;
  control_id: number;
  department_id: number;
  status: "not_started" | "partial" | "compliant" | "not_applicable";
  evidence_summary: string | null;
  last_reviewed_at: string | null;
  owner_user_id: number | null;
};

export type Department = { id: number; code: string | null; name_ar: string; name_en: string };

export type CurrentUser = {
  id: number;
  email: string;
  full_name_ar: string;
  role: "admin" | "auditor" | "owner" | "viewer";
  department_id: number | null;
};

export type DashboardStats = {
  total_controls: number;
  compliant: number;
  partial: number;
  not_started: number;
  not_applicable: number;
  compliance_rate: number;
};
