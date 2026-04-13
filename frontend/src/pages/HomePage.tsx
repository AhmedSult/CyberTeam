import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  type ComplianceRecord,
  type Control,
  type CurrentUser,
  type DashboardStats,
  type Department,
  type Framework,
} from "../api";
import { AssistantChatPanel } from "../components/AssistantChatPanel";
import { Spinner } from "../components/Spinner";

/** وثيقة الضوابط ECC-2-2024 — CDN الهيئة */
const OFFICIAL_ECC_PDF =
  "https://cdn.nca.gov.sa/api/files/public/upload/29a9e86a-595f-4af9-8db5-88715a458a14_ECC-2-2024---NCA.pdf";
/** الدليل الإرشادي GECC المرفق مع الخادم (نفس المجلد data/) */
const GECC_GUIDE_PDF_LOCAL = "/api/reference/gecc-implementation-guide-ar.pdf";

const DEFAULT_TABLE_PAGE_SIZE = 15;
const TABLE_PAGE_SIZE_OPTIONS = [10, 15, 25, 50] as const;

const statusLabels: Record<string, string> = {
  not_started: "لم يبدأ",
  partial: "جزئي",
  compliant: "ممتثل",
  not_applicable: "لا ينطبق",
};

/** أيقونة هدف (دائرة مركزية) */
function IconGoalMark() {
  return (
    <svg className="table-action-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <circle cx="12" cy="12" r="3.25" />
      <circle cx="12" cy="12" r="7" strokeDasharray="2 2" opacity="0.85" />
      <circle cx="12" cy="12" r="10.25" opacity="0.45" />
    </svg>
  );
}

/** أيقونة مستند / نص ضابط */
function IconDocClause() {
  return (
    <svg className="table-action-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M7 3.5h6l4.5 4.5V20.5a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1z" strokeLinejoin="round" />
      <path d="M13 3.5v4.5h4.5" strokeLinejoin="round" />
      <path d="M8.5 12.5h7M8.5 15.5h7M8.5 18.5h4" strokeLinecap="round" />
    </svg>
  );
}

/** مجال (حوكمة / تعزيز / …) */
function IconDomain() {
  return (
    <svg className="th-heading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M4 10.5L12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z" strokeLinejoin="round" />
    </svg>
  );
}

function IconControlId() {
  return (
    <svg className="th-heading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M7 7h10M7 12h10M7 17h6" strokeLinecap="round" />
      <rect x="3" y="4" width="18" height="16" rx="2" />
    </svg>
  );
}

function IconControlName() {
  return (
    <svg className="th-heading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
      <path d="M5 20.5v-1.2a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v1.2" strokeLinecap="round" />
    </svg>
  );
}

function IconDescription() {
  return (
    <svg className="th-heading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M8 10h8M8 14h5" strokeLinecap="round" />
      <rect x="5" y="4" width="14" height="16" rx="2" />
    </svg>
  );
}

/** أدلة / إثبات إرشادي (GECC) */
function IconEvidenceGuide({ size = "head" as "head" | "cell" }) {
  const cls = size === "cell" ? "table-action-icon-svg" : "th-heading-icon";
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M9 11l3 3L22 4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" strokeLinejoin="round" />
    </svg>
  );
}

function Stat({ title, value, accent }: { title: string; value: string | number; accent?: string }) {
  const stripe = accent || "var(--nca-green)";
  return (
    <div className="stat-card" style={{ borderRight: `3px solid ${stripe}` }}>
      <div className="stat-card-title">{title}</div>
      <div className="stat-card-value" style={{ color: accent || "var(--text)" }}>
        {value}
      </div>
    </div>
  );
}

type Props = {
  err: string | null;
  stats: DashboardStats | null;
  frameworks: Framework[];
  fw: number | "";
  setFw: (v: number | "") => void;
  depts: Department[];
  deptFilter: number | "";
  setDeptFilter: (v: number | "") => void;
  loading: boolean;
  loadData: () => void;
  gapLoading: boolean;
  gap: string | null;
  runGap: (opts?: { control_ids?: number[] }) => void | Promise<void>;
  /** يُستدعى عند تغيير بحث/تصفية الجدول لإبطال ملخص فجوات قديم */
  onComplianceTableFilterChange?: () => void;
  patchingRecordId: number | null;
  records: ComplianceRecord[];
  controlById: Map<number, Control>;
  deptById: Map<number, Department>;
  updateStatus: (rec: ComplianceRecord, status: ComplianceRecord["status"]) => void;
  chat: string;
  setChat: (v: string) => void;
  chatLog: { role: "user" | "ai"; text: string }[];
  sendChat: () => void | Promise<void>;
  chatSending: boolean;
  currentUser: CurrentUser | null;
};

export function HomePage({
  err,
  stats,
  frameworks,
  fw,
  setFw,
  depts,
  deptFilter,
  setDeptFilter,
  loading,
  loadData,
  gapLoading,
  gap,
  runGap,
  onComplianceTableFilterChange,
  records,
  controlById,
  deptById,
  patchingRecordId,
  updateStatus,
  chat,
  setChat,
  chatLog,
  sendChat,
  chatSending,
  currentUser,
}: Props) {
  const [explainOpen, setExplainOpen] = useState(false);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainText, setExplainText] = useState<string | null>(null);
  const [explainPdfUrl, setExplainPdfUrl] = useState<string>("");
  const [explainErr, setExplainErr] = useState<string | null>(null);
  /** نافذة تفصيل: هدف أو نص الضابط أو إرشاد أدلة */
  const [controlDetailModal, setControlDetailModal] = useState<
    null | { mode: "objective" | "clause" | "evidence"; control: Control }
  >(null);

  const [tableSearch, setTableSearch] = useState("");
  const [filterControlRef, setFilterControlRef] = useState("");
  const [filterStandardTitle, setFilterStandardTitle] = useState("");
  const [filterDomain, setFilterDomain] = useState("");
  const [tablePage, setTablePage] = useState(1);
  const [tablePageSize, setTablePageSize] = useState(DEFAULT_TABLE_PAGE_SIZE);
  const [gapScopeHint, setGapScopeHint] = useState<string | null>(null);
  const prevTableFilters = useRef({
    tableSearch,
    filterControlRef,
    filterStandardTitle,
    filterDomain,
  });
  const [deptFormErr, setDeptFormErr] = useState<string | null>(null);
  const [deptSubmitting, setDeptSubmitting] = useState(false);
  const [newDeptCode, setNewDeptCode] = useState("");
  const [newDeptNameAr, setNewDeptNameAr] = useState("");
  const [newDeptNameEn, setNewDeptNameEn] = useState("");

  const selectedFw = typeof fw === "number" ? frameworks.find((f) => f.id === fw) : undefined;

  const recordsInScope = useMemo(
    () => records.filter((r) => controlById.has(r.control_id)),
    [records, controlById]
  );

  const { controlRefOptions, standardTitleOptions } = useMemo(() => {
    const refs = new Set<string>();
    const titles = new Set<string>();
    for (const r of recordsInScope) {
      const c = controlById.get(r.control_id);
      if (!c) continue;
      refs.add(c.control_ref);
      if (c.standard_title_ar?.trim()) titles.add(c.standard_title_ar.trim());
    }
    return {
      controlRefOptions: [...refs].sort((a, b) => a.localeCompare(b, "ar", { numeric: true })),
      standardTitleOptions: [...titles].sort((a, b) => a.localeCompare(b, "ar")),
    };
  }, [recordsInScope, controlById]);

  const domainOptions = useMemo(() => {
    const s = new Set<string>();
    for (const r of recordsInScope) {
      const c = controlById.get(r.control_id);
      const dom = c?.domain_ar?.trim();
      if (dom) s.add(dom);
    }
    return [...s].sort((a, b) => a.localeCompare(b, "ar"));
  }, [recordsInScope, controlById]);

  const filteredTableRecords = useMemo(() => {
    const q = tableSearch.trim().toLowerCase();
    const tokens = q ? q.split(/\s+/).filter(Boolean) : [];
    return recordsInScope.filter((rec) => {
      const c = controlById.get(rec.control_id);
      if (!c) return false;
      if (filterControlRef && c.control_ref !== filterControlRef) return false;
      if (filterStandardTitle && (c.standard_title_ar || "").trim() !== filterStandardTitle) return false;
      if (filterDomain && (c.domain_ar || "").trim() !== filterDomain) return false;
      if (tokens.length === 0) return true;
      const hay = [
        c.domain_ar,
        c.control_ref,
        c.title_ar,
        c.title_en,
        c.standard_title_ar,
        c.objective_ar,
        c.implementation_guidance_ar,
        c.evidence_guidance_ar,
        c.category,
      ]
        .filter(Boolean)
        .join("\n")
        .toLowerCase();
      return tokens.every((t) => hay.includes(t));
    });
  }, [recordsInScope, controlById, tableSearch, filterControlRef, filterStandardTitle, filterDomain]);

  const gapAnalysisControlIds = useMemo(() => {
    const s = new Set<number>();
    for (const r of filteredTableRecords) s.add(r.control_id);
    return [...s];
  }, [filteredTableRecords]);

  const tableTotalPages = Math.max(1, Math.ceil(filteredTableRecords.length / tablePageSize) || 1);
  const tablePageClamped = Math.min(Math.max(1, tablePage), tableTotalPages);
  const paginatedRecords = useMemo(() => {
    const start = (tablePageClamped - 1) * tablePageSize;
    return filteredTableRecords.slice(start, start + tablePageSize);
  }, [filteredTableRecords, tablePageClamped, tablePageSize]);

  const tableRangeStart =
    filteredTableRecords.length === 0 ? 0 : (tablePageClamped - 1) * tablePageSize + 1;
  const tableRangeEnd = Math.min(tablePageClamped * tablePageSize, filteredTableRecords.length);

  useEffect(() => {
    setTablePage(1);
  }, [tableSearch, filterControlRef, filterStandardTitle, filterDomain, tablePageSize, fw, deptFilter]);

  useEffect(() => {
    const prev = prevTableFilters.current;
    const changed =
      prev.tableSearch !== tableSearch ||
      prev.filterControlRef !== filterControlRef ||
      prev.filterStandardTitle !== filterStandardTitle ||
      prev.filterDomain !== filterDomain;
    prevTableFilters.current = { tableSearch, filterControlRef, filterStandardTitle, filterDomain };
    if (!changed) return;
    setGapScopeHint(null);
    onComplianceTableFilterChange?.();
  }, [tableSearch, filterControlRef, filterStandardTitle, filterDomain, onComplianceTableFilterChange]);

  useEffect(() => {
    if (tablePage > tableTotalPages) setTablePage(tableTotalPages);
  }, [tablePage, tableTotalPages]);

  function runGapForFilteredTable() {
    if (gapAnalysisControlIds.length === 0) {
      setGapScopeHint("لا توجد سجلات ضمن التصفية الحالية لتشغيل تحليل الفجوات.");
      return;
    }
    setGapScopeHint(null);
    void runGap({ control_ids: gapAnalysisControlIds });
  }

  async function openFrameworkExplain() {
    if (typeof fw !== "number") return;
    setExplainOpen(true);
    setExplainLoading(true);
    setExplainText(null);
    setExplainErr(null);
    setExplainPdfUrl("");
    try {
      const r = await api.explainFramework(fw);
      setExplainText(r.explanation);
      setExplainPdfUrl(r.official_ecc_pdf_url);
    } catch (e) {
      setExplainErr(e instanceof Error ? e.message : String(e));
    } finally {
      setExplainLoading(false);
    }
  }

  function closeExplain() {
    setExplainOpen(false);
    setExplainText(null);
    setExplainErr(null);
  }

  function closeControlDetail() {
    setControlDetailModal(null);
  }

  async function submitNewDepartment(e: React.FormEvent) {
    e.preventDefault();
    if (currentUser?.role !== "admin") return;
    const na = newDeptNameAr.trim();
    const ne = newDeptNameEn.trim();
    if (!na || !ne) {
      setDeptFormErr("أدخل الاسم بالعربية والإنجليزية.");
      return;
    }
    setDeptFormErr(null);
    setDeptSubmitting(true);
    try {
      const code = newDeptCode.trim() || null;
      await api.createDepartment({
        name_ar: na,
        name_en: ne,
        code: code || undefined,
      });
      setNewDeptCode("");
      setNewDeptNameAr("");
      setNewDeptNameEn("");
      await loadData();
    } catch (err) {
      setDeptFormErr(err instanceof Error ? err.message : String(err));
    } finally {
      setDeptSubmitting(false);
    }
  }

  return (
    <div className="page-shell" dir="rtl">
      {err && <div className="page-banner page-banner--error">{err}</div>}

      <section className="home-hero-strip">
        <h1 className="home-hero-heading">مرحباً بك في لوحة التحكم</h1>
        <p className="home-hero-text">
          راقب مؤشرات الامتثال، صفِّ الضوابط حسب الإطار والإدارة، وشغّل تحليل الفجوات. للأسئلة التفصيلية عن الضوابط
          والأدلة استخدم <strong>المساعد الذكي</strong> من القائمة العلوية أو من قسم الدردشة أسفل الصفحة.
        </p>
      </section>

      <section className="grid-stats">
        <Stat title="إجمالي الضوابط" value={stats?.total_controls ?? "—"} />
        <Stat title="ممتثل" value={stats?.compliant ?? "—"} accent="var(--success)" />
        <Stat title="جزئي" value={stats?.partial ?? "—"} accent="var(--warn)" />
        <Stat title="لم يبدأ" value={stats?.not_started ?? "—"} accent="var(--danger)" />
        <Stat title="مؤشر الامتثال (تقريبي)" value={stats ? `${stats.compliance_rate}%` : "—"} />
      </section>

      <div className="app-layout-row home-layout">
        <aside className="panel-aside">
          <h2 className="panel-heading">فلترة</h2>
          <div className="framework-filter-block">
            <label className="field-label">
              الإطار
              <select
                className="field-input"
                value={fw}
                disabled={loading}
                onChange={(e) => setFw(e.target.value ? +e.target.value : "")}
              >
                <option value="">الكل</option>
                {frameworks.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name_ar} ({f.code})
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn-framework-explain"
              disabled={loading || typeof fw !== "number"}
              title={
                typeof fw !== "number"
                  ? "اختر إطاراً من القائمة أولاً لعرض شرح المعيار والضوابط"
                  : "شرح الإطار مع ربط وثيقة ECC الرسمية عند توفرها"
              }
              onClick={() => void openFrameworkExplain()}
            >
              شرح الإطار والمعيار
            </button>
            {typeof fw !== "number" && (
              <p className="framework-explain-hint">اختر إطاراً محدداً (ليس «الكل») لتفعيل الشرح.</p>
            )}
          </div>
          <label className="field-label">
            الإدارة
            <select
              className="field-input"
              value={deptFilter}
              disabled={loading}
              onChange={(e) => setDeptFilter(e.target.value ? +e.target.value : "")}
            >
              <option value="">الكل</option>
              {depts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.code ? `[${d.code}] ` : ""}
                  {d.name_ar}
                </option>
              ))}
            </select>
          </label>
          {currentUser?.role === "admin" && (
            <form className="dept-create-form card-elevated" onSubmit={(e) => void submitNewDepartment(e)}>
              <h3 className="panel-heading" style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>
                إضافة إدارة (ترميز)
              </h3>
              <label className="field-label">
                الترميز (اختياري)
                <input
                  className="field-input"
                  placeholder="مثل: HR أو SOC"
                  value={newDeptCode}
                  disabled={deptSubmitting}
                  onChange={(e) => setNewDeptCode(e.target.value.toUpperCase())}
                  autoComplete="off"
                />
              </label>
              <label className="field-label">
                الاسم بالعربية
                <input
                  className="field-input"
                  value={newDeptNameAr}
                  disabled={deptSubmitting}
                  onChange={(e) => setNewDeptNameAr(e.target.value)}
                  required
                />
              </label>
              <label className="field-label">
                الاسم بالإنجليزية
                <input
                  className="field-input"
                  value={newDeptNameEn}
                  disabled={deptSubmitting}
                  onChange={(e) => setNewDeptNameEn(e.target.value)}
                  required
                />
              </label>
              {deptFormErr && <p className="framework-explain-hint" style={{ color: "var(--danger)" }}>{deptFormErr}</p>}
              <button type="submit" className="btn-secondary btn-block btn-with-spinner" disabled={deptSubmitting}>
                {deptSubmitting && <Spinner tone="muted" />}
                {deptSubmitting ? "جاري الحفظ…" : "حفظ الإدارة"}
              </button>
            </form>
          )}
          <button type="button" className="btn-secondary btn-block btn-with-spinner" onClick={() => void loadData()} disabled={loading}>
            {loading && <Spinner tone="muted" />}
            {loading ? "جاري تحديث البيانات…" : "تحديث البيانات"}
          </button>
          <p className="framework-explain-hint" style={{ marginTop: "0.75rem" }}>
            <a href={GECC_GUIDE_PDF_LOCAL} target="_blank" rel="noopener noreferrer">
              فتح الدليل الإرشادي GECC-1:2023 (PDF)
            </a>
            {" · "}
            <a href={OFFICIAL_ECC_PDF} target="_blank" rel="noopener noreferrer">
              وثيقة الضوابط ECC-2-2024
            </a>
          </p>

          <h2 className="panel-heading panel-heading--spaced">تحليل الفجوات (AI)</h2>
          <p className="framework-explain-hint" style={{ marginTop: 0 }}>
            يُحلّل الضوابط التي تظهر سجلاتها في الجدول بعد اختيار الإطار والإدارة والبحث وتصفية الضابط/المعيار.
          </p>
          <button
            type="button"
            className="btn-primary btn-block btn-with-spinner"
            onClick={() => runGapForFilteredTable()}
            disabled={gapLoading}
            aria-busy={gapLoading}
          >
            {gapLoading && <Spinner tone="inverse" />}
            {gapLoading ? "جاري التحليل…" : "تشغيل التحليل"}
          </button>
          {gapLoading && (
            <div className="inline-loading">
              <Spinner tone="muted" />
              <span>يتم تحليل الفجوات الآن؛ قد يستغرق ذلك بضع ثوانٍ إذا وُجد نموذج لغوي.</span>
            </div>
          )}
          {gapScopeHint && !gapLoading && (
            <p className="framework-explain-hint" style={{ color: "var(--danger)" }}>
              {gapScopeHint}
            </p>
          )}
          {gap && !gapLoading && <p className="ai-summary-box">{gap}</p>}
        </aside>

        <main className="panel-main">
          <h2 className="panel-heading">سجلات الامتثال</h2>

          <div className="table-toolbar card-elevated">
            <div className="table-toolbar-row">
              <label className="table-toolbar-field table-toolbar-field--grow">
                <span className="table-toolbar-label">بحث في النص</span>
                <input
                  type="search"
                  className="field-input table-toolbar-input"
                  placeholder="مرجع الضابط، المعيار، العنوان، الهدف، نص الضابط…"
                  value={tableSearch}
                  disabled={loading}
                  onChange={(e) => setTableSearch(e.target.value)}
                  autoComplete="off"
                />
              </label>
            </div>
            <div className="table-toolbar-row table-toolbar-row--filters">
              <label className="table-toolbar-field">
                <span className="table-toolbar-label">تصفية حسب الضابط</span>
                <select
                  className="field-input table-toolbar-select"
                  value={filterControlRef}
                  disabled={loading}
                  onChange={(e) => setFilterControlRef(e.target.value)}
                >
                  <option value="">كل الضوابط</option>
                  {controlRefOptions.map((ref) => (
                    <option key={ref} value={ref}>
                      {ref}
                    </option>
                  ))}
                </select>
              </label>
              <label className="table-toolbar-field">
                <span className="table-toolbar-label">تصفية حسب المعيار</span>
                <select
                  className="field-input table-toolbar-select"
                  value={filterStandardTitle}
                  disabled={loading}
                  onChange={(e) => setFilterStandardTitle(e.target.value)}
                >
                  <option value="">كل المعايير</option>
                  {standardTitleOptions.map((t) => (
                    <option key={t} value={t}>
                      {t.length > 70 ? `${t.slice(0, 67)}…` : t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="table-toolbar-field">
                <span className="table-toolbar-label">تصفية حسب المجال</span>
                <select
                  className="field-input table-toolbar-select"
                  value={filterDomain}
                  disabled={loading}
                  onChange={(e) => setFilterDomain(e.target.value)}
                >
                  <option value="">كل المجالات</option>
                  {domainOptions.map((dom) => (
                    <option key={dom} value={dom}>
                      {dom}
                    </option>
                  ))}
                </select>
              </label>
              <label className="table-toolbar-field">
                <span className="table-toolbar-label">عدد الصفوف</span>
                <select
                  className="field-input table-toolbar-select table-toolbar-select--narrow"
                  value={tablePageSize}
                  disabled={loading}
                  onChange={(e) => setTablePageSize(+e.target.value)}
                >
                  {TABLE_PAGE_SIZE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="table-toolbar-meta">
              {filteredTableRecords.length === 0
                ? "لا توجد سجلات تطابق التصفية الحالية."
                : `عرض ${tableRangeStart}–${tableRangeEnd} من ${filteredTableRecords.length} سجلًا — الصفحة ${tablePageClamped} من ${tableTotalPages}`}
            </p>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="th-with-icon">
                    <span className="th-icon-wrap" title="المجال (حوكمة، تعزيز، صمود، …)">
                      <IconDomain />
                    </span>
                    <span className="th-label">المجال</span>
                  </th>
                  <th className="th-with-icon">
                    <span className="th-icon-wrap" title="رقم الضابط (مثل ECC-1-1-1)">
                      <IconControlId />
                    </span>
                    <span className="th-label">الضابط</span>
                  </th>
                  <th className="th-with-icon">
                    <span className="th-icon-wrap" title="اسم الضابط">
                      <IconControlName />
                    </span>
                    <span className="th-label">الاسم</span>
                  </th>
                  <th>المعيار</th>
                  <th className="th-with-icon th-with-icon--narrow">
                    <span className="th-icon-wrap" title="الوصف / الهدف التنظيمي">
                      <IconDescription />
                    </span>
                    <span className="th-label">وصف</span>
                  </th>
                  <th className="th-with-icon th-with-icon--narrow">
                    <span className="th-icon-wrap" title="نص المطلب (الضابط)">
                      <IconDocClause />
                    </span>
                    <span className="th-label">مطلب</span>
                  </th>
                  <th className="th-with-icon th-with-icon--narrow">
                    <span className="th-icon-wrap" title="إرشادات الأدلة (GECC)">
                      <IconEvidenceGuide size="head" />
                    </span>
                    <span className="th-label">دليل</span>
                  </th>
                  <th>الإدارة</th>
                  <th>الحالة</th>
                  <th>ملخص الأدلة</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRecords.map((rec) => {
                  const c = controlById.get(rec.control_id);
                  const d = deptById.get(rec.department_id);
                  return (
                    <tr key={rec.id}>
                      <td>
                        <span className="domain-pill">{c?.domain_ar ?? "—"}</span>
                      </td>
                      <td>
                        <strong>{c?.control_ref}</strong>
                      </td>
                      <td className="td-wrap td-compact-title" title={c?.title_ar}>
                        {c?.title_ar ?? "—"}
                      </td>
                      <td className="td-wrap">{c?.standard_title_ar ?? "—"}</td>
                      <td className="td-icon-cell">
                        <button
                          type="button"
                          className="btn-table-icon"
                          disabled={!c?.objective_ar}
                          title={c?.objective_ar ? "عرض الهدف والوصف التنظيمي" : "لا يوجد وصف مسجّل"}
                          aria-label="عرض الوصف والهدف"
                          onClick={() => c?.objective_ar && setControlDetailModal({ mode: "objective", control: c })}
                        >
                          <IconGoalMark />
                        </button>
                      </td>
                      <td className="td-icon-cell">
                        <button
                          type="button"
                          className="btn-table-icon btn-table-icon--doc"
                          disabled={!c?.implementation_guidance_ar}
                          title={c?.implementation_guidance_ar ? "عرض نص الضابط (المطلب)" : "لا يوجد نص مسجّل"}
                          aria-label="عرض نص الضابط"
                          onClick={() =>
                            c?.implementation_guidance_ar && setControlDetailModal({ mode: "clause", control: c })
                          }
                        >
                          <IconDocClause />
                        </button>
                      </td>
                      <td className="td-icon-cell">
                        <button
                          type="button"
                          className="btn-table-icon btn-table-icon--evidence"
                          disabled={!c?.evidence_guidance_ar}
                          title={c?.evidence_guidance_ar ? "عرض إرشادات الأدلة (GECC)" : "لا يوجد إرشاد مسجّل"}
                          aria-label="عرض إرشادات الأدلة"
                          onClick={() =>
                            c?.evidence_guidance_ar && setControlDetailModal({ mode: "evidence", control: c })
                          }
                        >
                          <IconEvidenceGuide size="cell" />
                        </button>
                      </td>
                      <td>
                        {d?.code ? <span className="dept-code-tag">{d.code}</span> : null} {d?.name_ar ?? "—"}
                      </td>
                      <td>{statusLabels[rec.status] ?? rec.status}</td>
                      <td className="td-evidence">{rec.evidence_summary ?? "—"}</td>
                      <td>
                        <div className="td-actions-cell">
                          {patchingRecordId === rec.id && <Spinner tone="muted" />}
                          <select
                            className="select-sm"
                            value={rec.status}
                            disabled={patchingRecordId === rec.id || loading}
                            aria-busy={patchingRecordId === rec.id}
                            onChange={(e) => void updateStatus(rec, e.target.value as ComplianceRecord["status"])}
                          >
                            {Object.entries(statusLabels).map(([k, v]) => (
                              <option key={k} value={k}>
                                {v}
                              </option>
                            ))}
                          </select>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {filteredTableRecords.length > 0 && (
            <nav className="table-pagination" aria-label="تصفح صفحات السجلات">
              <button
                type="button"
                className="btn-secondary btn-pagination"
                disabled={loading || tablePageClamped <= 1}
                onClick={() => setTablePage((p) => Math.max(1, p - 1))}
              >
                السابق
              </button>
              <span className="table-pagination-status">
                {tablePageClamped} / {tableTotalPages}
              </span>
              <button
                type="button"
                className="btn-secondary btn-pagination"
                disabled={loading || tablePageClamped >= tableTotalPages}
                onClick={() => setTablePage((p) => Math.min(tableTotalPages, p + 1))}
              >
                التالي
              </button>
            </nav>
          )}
        </main>
      </div>

      <section className="home-assistant-section" aria-labelledby="home-assistant-heading">
        <div className="home-assistant-intro card-elevated">
          <h2 id="home-assistant-heading" className="home-assistant-main-title">
            المساعد الذكي
          </h2>
          <p className="home-assistant-intro-text">
            نفس محادثة صفحة المساعد متاحة هنا لتسأل عن <strong>المعايير</strong> والضوابط والأدلة دون مغادرة لوحة
            التحكم. المحادثة موحّدة بين هذه الصفحة وصفحة «المساعد الذكي» في الأعلى.
          </p>
          <div className="home-assistant-criteria">
            <h3 className="home-assistant-criteria-title">معايير وإرشادات سريعة</h3>
            <ul className="home-assistant-criteria-list">
              <li>
                <strong>حالات الامتثال في الجدول:</strong> لم يبدأ، جزئي، ممتثل، لا ينطبق — اسأل المساعد عن الفرق
                أو ما يلزم للانتقال من حالة لأخرى.
              </li>
              <li>
                <strong>الإطار في اللوحة:</strong> عند اختيار إطار من «الإطار»، تُحسب **لقطة الامتثال** و**تحليل
                الفجوات** و**إجابات المساعد** على ضوابط ذلك الإطار فقط — ثم اسأل مثلاً: «اقترح حلولاً للفجوات
                حسب تحليلي» أو «ما خطوتي التالية لضابط X؟».
              </li>
              <li>
                <strong>الأدلة:</strong> يمكن طلب أمثلة لأدلة مقبولة أو ملخص أدلة لسجل معيّن حسب بياناتك الحالية.
              </li>
              <li>
                <strong>Enter للإرسال، Shift+Enter</strong> لسطر جديد في مربع النص.
              </li>
              <li>
                <strong>النسبة وتحليل الفجوات:</strong> بعد «تشغيل التحليل» يُرسل المساعد نفس النص مع كل سؤال؛
                وتُحسب **النسب والحالات** حسب فلتر «الإدارة» و«الإطار» معاً (أو الكل إن تركتهما فارغين).
              </li>
            </ul>
            <p className="home-assistant-full-link">
              <Link to="/assistant">فتح صفحة المساعد الكاملة مع شرح أوسع</Link>
            </p>
          </div>
        </div>
        <AssistantChatPanel
          embed
          chat={chat}
          setChat={setChat}
          chatLog={chatLog}
          sendChat={sendChat}
          chatSending={chatSending}
        />
      </section>

      {controlDetailModal && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="control-detail-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeControlDetail();
          }}
        >
          <div className="modal-panel modal-panel--wide modal-panel--clause" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 id="control-detail-title" className="modal-title">
                {controlDetailModal.mode === "objective"
                  ? "الوصف / الهدف التنظيمي"
                  : controlDetailModal.mode === "clause"
                    ? "نص الضابط (المطلب)"
                    : "إرشادات الأدلة والإثبات"}
              </h2>
              <button type="button" className="modal-close" onClick={closeControlDetail} aria-label="إغلاق">
                ×
              </button>
            </div>
            <div className="modal-body">
              <p className="modal-pdf-links">
                <a href={GECC_GUIDE_PDF_LOCAL} target="_blank" rel="noopener noreferrer">
                  الدليل الإرشادي GECC-1:2023 (PDF)
                </a>
                {" · "}
                <a href={OFFICIAL_ECC_PDF} target="_blank" rel="noopener noreferrer">
                  وثيقة الضوابط ECC-2-2024
                </a>
              </p>
              {controlDetailModal.mode === "objective" ? (
                <>
                  <p className="modal-clause-intro">
                    الهدف التنظيمي للمعيار كما ورد في الوثيقة (مستخرج في المنصة). يوضح الغرض قبل بنود الضوابط
                    التفصيلية.
                  </p>
                  <div className="modal-clause-sections">
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">مرجع الضابط</h3>
                      <p className="modal-clause-value">
                        <strong>{controlDetailModal.control.control_ref}</strong>
                        {controlDetailModal.control.domain_ar ? (
                          <span className="modal-clause-meta"> — {controlDetailModal.control.domain_ar}</span>
                        ) : controlDetailModal.control.category ? (
                          <span className="modal-clause-meta"> — {controlDetailModal.control.category}</span>
                        ) : null}
                      </p>
                    </section>
                    {controlDetailModal.control.standard_title_ar && (
                      <section className="modal-clause-block">
                        <h3 className="modal-clause-heading">المعيار</h3>
                        <p className="modal-clause-value">{controlDetailModal.control.standard_title_ar}</p>
                      </section>
                    )}
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">الهدف</h3>
                      <div className="modal-clause-scroll modal-clause-scroll--objective">
                        {controlDetailModal.control.objective_ar}
                      </div>
                    </section>
                  </div>
                </>
              ) : controlDetailModal.mode === "clause" ? (
                <>
                  <p className="modal-clause-intro">
                    تفصيل الضابط كما هو مسجّل في المنصة: المرجع، المعيار، الهدف، ثم نص المطلب. للاستفسار التفصيلي
                    استخدم المساعد الذكي أسفل الصفحة.
                  </p>
                  <div className="modal-clause-sections">
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">مرجع الضابط</h3>
                      <p className="modal-clause-value">
                        <strong>{controlDetailModal.control.control_ref}</strong>
                        {controlDetailModal.control.category ? (
                          <span className="modal-clause-meta"> — {controlDetailModal.control.category}</span>
                        ) : null}
                      </p>
                    </section>
                    {controlDetailModal.control.standard_title_ar && (
                      <section className="modal-clause-block">
                        <h3 className="modal-clause-heading">المعيار (المكوّن الفرعي)</h3>
                        <p className="modal-clause-value">{controlDetailModal.control.standard_title_ar}</p>
                      </section>
                    )}
                    {controlDetailModal.control.objective_ar && (
                      <section className="modal-clause-block">
                        <h3 className="modal-clause-heading">الهدف</h3>
                        <p className="modal-clause-value modal-clause-value--muted">
                          {controlDetailModal.control.objective_ar}
                        </p>
                      </section>
                    )}
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">نص الضابط (المطلب)</h3>
                      <div className="modal-clause-scroll">{controlDetailModal.control.implementation_guidance_ar}</div>
                    </section>
                  </div>
                </>
              ) : (
                <>
                  <p className="modal-clause-intro">
                    توجيهات لأنواع الأدلة والإثبات المقترحة في مسار التنفيذ، بما يتماشى مع الدليل الإرشادي GECC؛
                    يُكمّلها ملخص الأدلة في عمود السجل لديك.
                  </p>
                  <div className="modal-clause-sections">
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">مرجع الضابط</h3>
                      <p className="modal-clause-value">
                        <strong>{controlDetailModal.control.control_ref}</strong>
                        {controlDetailModal.control.domain_ar ? (
                          <span className="modal-clause-meta"> — {controlDetailModal.control.domain_ar}</span>
                        ) : null}
                      </p>
                    </section>
                    {controlDetailModal.control.standard_title_ar && (
                      <section className="modal-clause-block">
                        <h3 className="modal-clause-heading">المعيار</h3>
                        <p className="modal-clause-value">{controlDetailModal.control.standard_title_ar}</p>
                      </section>
                    )}
                    <section className="modal-clause-block">
                      <h3 className="modal-clause-heading">إرشادات الأدلة</h3>
                      <div className="modal-clause-scroll">{controlDetailModal.control.evidence_guidance_ar}</div>
                    </section>
                  </div>
                </>
              )}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={closeControlDetail}>
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}

      {explainOpen && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="framework-explain-title">
          <div className="modal-panel modal-panel--wide">
            <div className="modal-header">
              <h2 id="framework-explain-title" className="modal-title">
                شرح الإطار{selectedFw ? `: ${selectedFw.name_ar}` : ""}
              </h2>
              <button type="button" className="modal-close" onClick={closeExplain} aria-label="إغلاق">
                ×
              </button>
            </div>
            <div className="modal-body">
              <p className="modal-pdf-links">
                <a href={explainPdfUrl || OFFICIAL_ECC_PDF} target="_blank" rel="noopener noreferrer">
                  فتح وثيقة ECC-2-2024 الرسمية (PDF) — الهيئة الوطنية للأمن السيبراني
                </a>
                {" · "}
                <a href="https://nca.gov.sa/ar/" target="_blank" rel="noopener noreferrer">
                  الموقع الرسمي nca.gov.sa
                </a>
              </p>
              {explainLoading && (
                <p className="modal-loading">
                  <Spinner tone="muted" /> جاري إعداد الشرح…
                </p>
              )}
              {explainErr && <p className="modal-error">{explainErr}</p>}
              {explainText != null && !explainLoading && (
                <div className="modal-explain-text">{explainText}</div>
              )}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={closeExplain}>
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
