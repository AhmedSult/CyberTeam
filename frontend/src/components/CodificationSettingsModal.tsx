import { useEffect, useState } from "react";
import { api, type CurrentUser, type Department } from "../api";
import { Spinner } from "./Spinner";

type Props = {
  open: boolean;
  onClose: () => void;
  depts: Department[];
  onDepartmentsChanged: () => void | Promise<void>;
  currentUser: CurrentUser | null;
};

export function CodificationSettingsModal({ open, onClose, depts, onDepartmentsChanged, currentUser }: Props) {
  const [code, setCode] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const isAdmin = currentUser?.role === "admin";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isAdmin) return;
    const na = nameAr.trim();
    const ne = nameEn.trim();
    if (!na || !ne) {
      setErr("أدخل الاسم بالعربية والإنجليزية.");
      return;
    }
    setErr(null);
    setSubmitting(true);
    try {
      const c = code.trim() || null;
      await api.createDepartment({
        name_ar: na,
        name_en: ne,
        code: c || undefined,
      });
      setCode("");
      setNameAr("");
      setNameEn("");
      await onDepartmentsChanged();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="modal-overlay codification-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="codification-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-panel modal-panel--codification" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 id="codification-modal-title" className="modal-title">
              إعدادات ترميز الإدارات
            </h2>
            <p className="codification-modal-sub">
              تعريف الإدارات ورموزها للفلترة وتتبع الامتثال حسب الوحدة التنظيمية.
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="إغلاق">
            ×
          </button>
        </div>

        <div className="codification-modal-body">
          <section className="codification-list-section" aria-labelledby="dept-list-heading">
            <h3 id="dept-list-heading" className="codification-section-title">
              الإدارات المعرّفة ({depts.length})
            </h3>
            {depts.length === 0 ? (
              <p className="codification-empty">لا توجد إدارات بعد — أضف أول إدارة من النموذج أدناه (صلاحية المسؤول).</p>
            ) : (
              <ul className="codification-dept-list">
                {depts.map((d) => (
                  <li key={d.id} className="codification-dept-item">
                    <span className="codification-dept-code">{d.code || "—"}</span>
                    <span className="codification-dept-names">
                      <strong>{d.name_ar}</strong>
                      <span className="codification-dept-en">{d.name_en}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {isAdmin ? (
            <form className="codification-form card-elevated" onSubmit={(e) => void onSubmit(e)}>
              <h3 className="codification-section-title">إضافة إدارة جديدة</h3>
              <label className="field-label">
                الترميز (اختياري)
                <input
                  className="field-input"
                  placeholder="مثل: HR أو SOC"
                  value={code}
                  disabled={submitting}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  autoComplete="off"
                />
              </label>
              <label className="field-label">
                الاسم بالعربية
                <input
                  className="field-input"
                  value={nameAr}
                  disabled={submitting}
                  onChange={(e) => setNameAr(e.target.value)}
                  required
                />
              </label>
              <label className="field-label">
                الاسم بالإنجليزية
                <input
                  className="field-input"
                  value={nameEn}
                  disabled={submitting}
                  onChange={(e) => setNameEn(e.target.value)}
                  required
                />
              </label>
              {err && <p className="codification-form-err">{err}</p>}
              <button type="submit" className="btn-primary btn-block btn-with-spinner" disabled={submitting}>
                {submitting && <Spinner tone="inverse" />}
                {submitting ? "جاري الحفظ…" : "حفظ الإدارة"}
              </button>
            </form>
          ) : (
            <p className="codification-readonly-hint">لإضافة إدارات جديدة يلزم صلاحية مسؤول النظام.</p>
          )}
        </div>
      </div>
    </div>
  );
}
