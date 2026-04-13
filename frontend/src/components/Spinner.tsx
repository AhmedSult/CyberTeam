type Props = {
  /** inverse: فاتح على خلفية خضراء — muted: على خلفية فاتحة */
  tone?: "inverse" | "muted";
  className?: string;
};

export function Spinner({ tone = "muted", className = "" }: Props) {
  return (
    <span
      className={`ui-spinner ui-spinner--${tone} ${className}`.trim()}
      role="status"
      aria-label="جاري التحميل"
    />
  );
}
