import { PLATFORM_NAME_AR } from "../brand";
import { AssistantChatPanel } from "../components/AssistantChatPanel";

type Msg = { role: "user" | "ai"; text: string };

type Props = {
  chat: string;
  setChat: (v: string) => void;
  chatLog: Msg[];
  sendChat: () => void | Promise<void>;
  chatSending: boolean;
};

export function AssistantPage({ chat, setChat, chatLog, sendChat, chatSending }: Props) {
  return (
    <div className="page-shell page-shell--enter assistant-page" dir="rtl">
      <div className="assistant-layout">
        <section className="assistant-guide card-elevated">
          <h1 className="assistant-title">مساعد {PLATFORM_NAME_AR}</h1>
          <p className="assistant-lead">
            المساعد يجمع بين <strong>نموذج لغوي (GPT)</strong> لشرح المعايير وإرشادك، وبين{" "}
            <strong>منطق المنصة</strong>: نسب الامتثال وسجلاتك وتحليل الفجوات (من الصفحة الرئيسية) ومقتطفات من وثيقة{" "}
            <strong>ECC-2-2024</strong> الرسمية للهيئة — عند تشغيل الخادم مع مفتاح OpenAI وفهرس ECC.
          </p>
          <h2 className="assistant-subtitle">كيف تستخدم الدردشة؟</h2>
          <ul className="assistant-tips">
            <li>
              اكتب سؤالك في المربع أسفل الصفحة ثم اضغط <strong>إرسال</strong> أو Enter.
            </li>
            <li>
              جرّب أسئلة مثل: «ما الفرق بين حالة جزئي وممتثل؟» أو «اقترح أدلة لضابط التحكم في الوصول».
            </li>
            <li>يمكنك متابعة الحوار: المساعد يأخذ سياق المحادثة ضمن نفس الجلسة في الواجهة.</li>
            <li>إن ظهرت رسالة خطأ، تحقق من تشغيل الخادم وإعدادات المفتاح في ملف بيئة الخلفية.</li>
            <li>
              من <strong>الصفحة الرئيسية</strong> يُرسل مع المحادثة آخر «تحليل الفجوات» وفلتر الإدارة — اسأل عن
              نسبتك أو مشاكلك بعد تشغيل التحليل هناك.
            </li>
            <li>
              استيراد الضوابط من جداول ورفع الأدلة يحدّث <strong>مدخلات النظام</strong>؛ المساعد يربط شرح ECC بوضعك
              حسب ما يظهر في اللقطة المرسلة تلقائياً مع السؤال.
            </li>
            <li>
              من <strong>الصفحة الرئيسية</strong> يمكنك أيضاً <strong>تحليل ملف PDF/Excel</strong> (استخراج + RAG + نموذج
              لغوي) وتنزيل <strong>تقرير امتثال PDF</strong> حسب نفس فلاتر الإطار والإدارة.
            </li>
          </ul>
        </section>

        <AssistantChatPanel
          chat={chat}
          setChat={setChat}
          chatLog={chatLog}
          sendChat={sendChat}
          chatSending={chatSending}
        />
      </div>
    </div>
  );
}
