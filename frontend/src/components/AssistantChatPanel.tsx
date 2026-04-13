import { useRef, useEffect } from "react";
import { Spinner } from "./Spinner";

export type ChatMsg = { role: "user" | "ai"; text: string };

const DEFAULT_SUGGESTED_PROMPTS = [
  "وش ناقصني في ECC حسب لقطة الامتثال وتحليل الفجوات؟",
  "هل أنا متوافق مع الضابط حسب بيانات المنصة؟",
  "ما الفرق بين حالة جزئي وممتثل عملياً؟",
];

type Props = {
  chat: string;
  setChat: (v: string) => void;
  chatLog: ChatMsg[];
  sendChat: () => void | Promise<void>;
  chatSending: boolean;
  /** وضع مدمج في الصفحة الرئيسية — ارتفاع أصغر للرسائل */
  embed?: boolean;
  /** اقتراحات سريعة تملأ مربع الإدخال */
  suggestedPrompts?: string[];
};

export function AssistantChatPanel({
  chat,
  setChat,
  chatLog,
  sendChat,
  chatSending,
  embed,
  suggestedPrompts = DEFAULT_SUGGESTED_PROMPTS,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog, chatSending]);

  const chatClass = embed ? "assistant-chat card-elevated assistant-chat--embed" : "assistant-chat card-elevated";

  return (
    <section className={chatClass}>
      <h2 className={embed ? "assistant-embed-chat-heading" : "visually-hidden"}>{embed ? "المحادثة" : "محادثة"}</h2>
      <div className="assistant-messages" role="log" aria-live="polite">
        {chatLog.length === 0 && !chatSending && (
          <p className="assistant-empty">
            {embed
              ? "اكتب سؤالك أدناه — يمكنك الاستفسار عن المعايير، الضوابط، والأدلة."
              : "ابدأ بكتابة سؤالك أدناه — ستظهر الرسائل هنا."}
          </p>
        )}
        {chatLog.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
            <span className="chat-bubble-label">{m.role === "user" ? "أنت" : "المساعد"}</span>
            <div className="chat-bubble-text">{m.text}</div>
          </div>
        ))}
        {chatSending && (
          <div className="chat-bubble chat-bubble--ai chat-bubble--typing">
            <span className="chat-bubble-label">المساعد</span>
            <div className="chat-bubble-typing-row">
              <Spinner tone="muted" />
              <span>جاري إعداد الرد…</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      {suggestedPrompts.length > 0 && (
        <div className="assistant-suggested" aria-label="أسئلة مقترحة">
          {suggestedPrompts.map((p) => (
            <button
              key={p}
              type="button"
              className="btn-suggested-prompt"
              disabled={chatSending}
              onClick={() => setChat(p)}
            >
              {p}
            </button>
          ))}
        </div>
      )}
      <div className="assistant-compose">
        <textarea
          className="field-input assistant-textarea"
          placeholder="اسأل عن معيار، ضابط، إثبات، أو خطوات تطبيق..."
          value={chat}
          disabled={chatSending}
          onChange={(e) => setChat(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !chatSending) {
              e.preventDefault();
              void sendChat();
            }
          }}
          rows={embed ? 2 : 3}
        />
        <button
          type="button"
          className="btn-primary assistant-send btn-with-spinner"
          onClick={() => void sendChat()}
          disabled={chatSending}
          aria-busy={chatSending}
        >
          {chatSending && <Spinner tone="inverse" />}
          {chatSending ? "جاري الإرسال…" : "إرسال"}
        </button>
      </div>
    </section>
  );
}
