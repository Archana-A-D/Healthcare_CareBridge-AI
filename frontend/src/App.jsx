import { useEffect, useState } from "react";
import { askQuestion, uploadDischargeSummary, translateSummary } from "./services/api";
import "./App.css";

const copy = {
  en: {
    subtitle: "Discharge Summary Explainer", intro: "Understand discharge information clearly, in one place.",
    upload: "Upload a discharge summary", uploadHint: "Choose a PDF or drag it here", choose: "Choose PDF",
    process: "Process document", processing: "Processing...", remove: "Remove file",
    downloadReport: "Download details (.txt)", printPdf: "Print / Save as PDF", ready: "Discharge details are ready",
    patient: "Patient overview", alert: "Important information", meds: "Medication schedule",
    medicine: "Medicine", dosage: "Dose & instructions", duration: "Duration", timing: "Timing",
    follow: "Follow-up details", instructions: "Discharge instructions",
    chat: "Ask about this document", chatHint: "Ask a question about this discharge summary...", send: "Send",
    languageNote: "This translates the extracted discharge details. Check medicine names and doses against the original PDF.",
    empty: "Select and process a PDF to show the discharge details here.", patientName: "Patient name",
    patientId: "Patient ID", ageSex: "Age / sex", hospital: "Hospital", department: "Department",
    admission: "Admission date", discharge: "Discharge date", summary: "Summary", followDate: "Follow-up date",
    followDept: "Department", you: "You", chatWelcome: "Ask about medications, follow-up, or instructions in this summary.",
    source: "Source: Page", uploadError: "Please select a PDF file.", askError: "Could not get an answer. Please try again.", humanReview: "Please contact a qualified clinician for human review."
  },
  ml: {
    subtitle: "ഡിസ്ചാർജ് സംഗ്രഹ വിശദീകരണം", intro: "ഡിസ്ചാർജ് വിവരങ്ങൾ ലളിതമായി മനസ്സിലാക്കുക.",
    upload: "ഡിസ്ചാർജ് സംഗ്രഹം അപ്‌ലോഡ് ചെയ്യുക", uploadHint: "PDF തിരഞ്ഞെടുക്കുക അല്ലെങ്കിൽ ഇവിടെ ഇടുക", choose: "PDF തിരഞ്ഞെടുക്കുക", process: "രേഖ പ്രോസസ്സ് ചെയ്യുക", processing: "പ്രോസസ്സ് ചെയ്യുന്നു...", remove: "ഫയൽ നീക്കം ചെയ്യുക", downloadReport: "വിശദാംശങ്ങൾ ഡൗൺലോഡ് ചെയ്യുക (.txt)", printPdf: "പ്രിന്റ് ചെയ്യുക / PDF ആയി സേവ് ചെയ്യുക", ready: "ഡിസ്ചാർജ് വിവരങ്ങൾ തയ്യാറാണ്",
    patient: "രോഗിയുടെ വിവരങ്ങൾ", alert: "പ്രധാനപ്പെട്ട വിവരം", meds: "മരുന്നുകളുടെ പട്ടിക", medicine: "മരുന്ന്",
    follow: "തുടർപരിചരണ വിവരങ്ങൾ", instructions: "ഡിസ്ചാർജ് നിർദ്ദേശങ്ങൾ",
    chat: "ഈ രേഖയെക്കുറിച്ച് ചോദിക്കുക", summary: "സംഗ്രഹം", patientName: "രോഗിയുടെ പേര്", patientId: "രോഗിയുടെ ഐഡി", humanReview: "യോഗ്യനായ ഡോക്ടറെയോ അടിയന്തര സേവനത്തെയോ ഉടൻ ബന്ധപ്പെടുക.",
    hospital: "ആശുപത്രി", department: "വിഭാഗം", admission: "പ്രവേശന തീയതി", discharge: "ഡിസ്ചാർജ് തീയതി",
    followDate: "തുടർപരിശോധന തീയതി", followDept: "വിഭാഗം", dosage: "ഡോസ്, നിർദ്ദേശങ്ങൾ", duration: "കാലയളവ്", timing: "സമയം", ageSex: "പ്രായം / ലിംഗം", chatHint: "ഈ ഡിസ്ചാർജ് സംഗ്രഹത്തെക്കുറിച്ച് ചോദിക്കുക...", chatWelcome: "മരുന്നുകൾ, തുടർപരിശോധന, നിർദ്ദേശങ്ങൾ എന്നിവയെക്കുറിച്ച് ചോദിക്കുക.", languageNote: "ഇത് എടുത്തെടുത്ത ഡിസ്ചാർജ് വിവരങ്ങൾ വിവർത്തനം ചെയ്യുന്നു. മരുന്നുകളുടെ പേരും ഡോസും യഥാർത്ഥ PDF-ുമായി പരിശോധിക്കുക.", empty: "ഡിസ്ചാർജ് വിവരങ്ങൾ കാണാൻ PDF തിരഞ്ഞെടുത്ത് പ്രോസസ്സ് ചെയ്യുക.", send: "അയയ്ക്കുക", you: "നിങ്ങൾ", source: "ഉറവിടം: പേജ്"
  },
  ta: {
    subtitle: "வெளியேற்ற சுருக்க விளக்கம்", intro: "வெளியேற்றத் தகவல்களை எளிதாகப் புரிந்துகொள்ளுங்கள்.",
    upload: "வெளியேற்றச் சுருக்கத்தைப் பதிவேற்றவும்", uploadHint: "PDF-ஐத் தேர்ந்தெடுக்கவும் அல்லது இங்கே விடவும்", choose: "PDF தேர்வு", process: "ஆவணத்தைச் செயலாக்கு", processing: "செயலாக்கப்படுகிறது...", remove: "கோப்பை அகற்று", downloadReport: "விவரங்களைப் பதிவிறக்கவும் (.txt)", printPdf: "அச்சிடு / PDF ஆகச் சேமி", ready: "வெளியேற்ற விவரங்கள் தயார்",
    patient: "நோயாளர் விவரங்கள்", alert: "முக்கிய தகவல்", meds: "மருந்து அட்டவணை", medicine: "மருந்து",
    follow: "தொடர் பராமரிப்பு விவரங்கள்", instructions: "வெளியேற்ற வழிமுறைகள்",
    chat: "இந்த ஆவணத்தைப் பற்றிக் கேளுங்கள்", summary: "சுருக்கம்", patientName: "நோயாளியின் பெயர்", patientId: "நோயாளர் எண்", humanReview: "தகுதியான மருத்துவரையோ அவசர சேவையையோ உடனே அணுகவும்.",
    hospital: "மருத்துவமனை", department: "பிரிவு", admission: "சேர்க்கை தேதி", discharge: "வெளியேற்ற தேதி",
    followDate: "தொடர் பரிசோதனை தேதி", followDept: "பிரிவு", dosage: "அளவு மற்றும் வழிமுறைகள்", duration: "கால அளவு", timing: "நேரம்", ageSex: "வயது / பாலினம்", chatHint: "இந்த வெளியேற்றச் சுருக்கத்தைப் பற்றி கேளுங்கள்...", chatWelcome: "மருந்துகள், தொடர் பரிசோதனை அல்லது வழிமுறைகள் பற்றி கேளுங்கள்.", languageNote: "இது எடுக்கப்பட்ட வெளியேற்ற விவரங்களை மொழிபெயர்க்கும். மருந்துப் பெயர்களையும் அளவுகளையும் அசல் PDF-உடன் சரிபார்க்கவும்.", empty: "வெளியேற்ற விவரங்களைக் காண PDF-ஐத் தேர்ந்தெடுத்து செயலாக்கவும்.", send: "அனுப்பு", you: "நீங்கள்", source: "ஆதாரம்: பக்கம்"
  },
  hi: {
    subtitle: "डिस्चार्ज सारांश समझें", intro: "डिस्चार्ज की जानकारी सरल भाषा में समझें।",
    upload: "डिस्चार्ज सारांश अपलोड करें", uploadHint: "PDF चुनें या यहाँ छोड़ें", choose: "PDF चुनें", process: "दस्तावेज़ प्रोसेस करें", processing: "प्रोसेस हो रहा है...", remove: "फ़ाइल हटाएँ", downloadReport: "विवरण डाउनलोड करें (.txt)", printPdf: "प्रिंट करें / PDF के रूप में सेव करें", ready: "डिस्चार्ज विवरण तैयार हैं",
    patient: "मरीज़ की जानकारी", alert: "महत्वपूर्ण जानकारी", meds: "दवाओं की सूची", medicine: "दवा",
    follow: "फ़ॉलो-अप विवरण", instructions: "डिस्चार्ज निर्देश",
    chat: "इस दस्तावेज़ के बारे में पूछें", summary: "सारांश", patientName: "मरीज़ का नाम", patientId: "मरीज़ आईडी", humanReview: "तुरंत किसी योग्य चिकित्सक या आपातकालीन सेवा से संपर्क करें।",
    hospital: "अस्पताल", department: "विभाग", admission: "भर्ती की तारीख", discharge: "डिस्चार्ज की तारीख",
    followDate: "फ़ॉलो-अप की तारीख", followDept: "विभाग", dosage: "खुराक और निर्देश", duration: "अवधि", timing: "समय", ageSex: "उम्र / लिंग", chatHint: "इस डिस्चार्ज सारांश के बारे में पूछें...", chatWelcome: "दवाओं, फ़ॉलो-अप या निर्देशों के बारे में पूछें।", languageNote: "यह निकाली गई डिस्चार्ज जानकारी का अनुवाद करता है। दवा के नाम और खुराक मूल PDF से जाँचें।", empty: "डिस्चार्ज विवरण देखने के लिए PDF चुनें और प्रोसेस करें।", send: "भेजें", you: "आप", source: "स्रोत: पृष्ठ"
  }
};
const languages = [["en", "English"], ["ml", "\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02"], ["ta", "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"], ["hi", "\u0939\u093f\u0928\u094d\u0926\u0940"]];
const testCopy = {
  en: { title: "Tests to Complete", empty: "No tests are listed in the discharge summary." },
  ml: { title: "ചെയ്യേണ്ട പരിശോധനകൾ", empty: "ഡിസ്ചാർജ് സംഗ്രഹത്തിൽ പരിശോധനകൾ നൽകിയിട്ടില്ല." },
  ta: { title: "செய்ய வேண்டிய பரிசோதனைகள்", empty: "வெளியேற்றச் சுருக்கத்தில் பரிசோதனைகள் குறிப்பிடப்படவில்லை." },
  hi: { title: "कराए जाने वाले परीक्षण", empty: "डिस्चार्ज सारांश में कोई परीक्षण सूचीबद्ध नहीं है।" }
};

const dateLocales = { en: "en-GB", ml: "ml-IN", ta: "ta-IN", hi: "hi-IN" };
const missingDateText = { en: "Not stated", ml: "വ്യക്തമാക്കിയിട്ടില്ല", ta: "குறிப்பிடப்படவில்லை", hi: "उल्लेख नहीं है" };
function formatDisplayDate(value, language = "en") {
  if (value === null || value === undefined || !String(value).trim()) return missingDateText[language] || missingDateText.en;
  const raw = String(value).trim();
  const iso = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  const dayFirst = raw.match(/^(\d{1,2})[/.](\d{1,2})[/.](\d{4})$/);
  let date;
  if (iso) date = new Date(Date.UTC(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3])));
  else if (dayFirst) date = new Date(Date.UTC(Number(dayFirst[3]), Number(dayFirst[2]) - 1, Number(dayFirst[1])));
  else date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  return new Intl.DateTimeFormat(dateLocales[language] || dateLocales.en, { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(date);
}

function Section({ id, title, icon, children, tone = "blue", source, sourceLabel = "Source: Page" }) {
  return <section className={`flow-card ${tone}`} id={id}><div className="flow-card-heading"><span className="section-icon" aria-hidden="true">{icon}</span><h2>{title}</h2></div><div className="flow-card-body">{children}</div>{source && <div className="citation">{sourceLabel} {source}</div>}</section>;
}

function App() {
  const [language, setLanguage] = useState("en");
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryId, setSummaryId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sourceSummary, setSourceSummary] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const t = { ...copy.en, ...copy[language] };
  const testsText = { ...testCopy.en, ...testCopy[language] };

  useEffect(() => {
    if (!summaryId || language === "en") {
      setSummary(sourceSummary);
      setIsTranslating(false);
      return;
    }
    let active = true;
    setIsTranslating(true);
    setFileError("");
    translateSummary(summaryId, language)
      .then(({ summary: translated }) => { if (active) setSummary(translated); })
      .catch((error) => {
        if (active) {
          setSummary(sourceSummary);
          setFileError(`Translation failed; showing the original language. ${error.message}`);
          setLanguage("en");
        }
      })
      .finally(() => { if (active) setIsTranslating(false); });
    return () => { active = false; };
  }, [language, summaryId, sourceSummary]);

  const selectFile = (selectedFile) => {
    setFileError("");
    if (!selectedFile) return;
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setFileError(t.uploadError);
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setSummary(null);
    setSummaryId(null);
    setSourceSummary(null);
    setMessages([]);
  };

  const processFile = async () => {
    if (!file) { setFileError(t.uploadError); return; }
    setIsProcessing(true);
    setFileError("");
    try {
      const result = await uploadDischargeSummary(file);
      setSummaryId(result.summaryId);
      setSessionId(null);
      setSourceSummary(result.summary);
      setSummary(result.summary);
    } catch (error) {
      setFileError(error.message || "Upload failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadReport = () => {
    if (!summary) return;
    const formatDate = (date) => formatDisplayDate(date, language);
    const report = [
      "CareBridge-AI - Discharge Summary Details",
      `Patient: ${summary.patient.name}`,
      `Patient ID: ${summary.patient.patientId}`,
      `Age / Sex: ${summary.patient.age} / ${summary.patient.gender}`,
      `Hospital: ${summary.hospital.name}`,
      `Department: ${summary.hospital.department}`,
      `Admission date: ${formatDate(summary.admissionDate)}`,
      `Discharge date: ${formatDate(summary.dischargeDate)}`,
      "", "SUMMARY", summary.summary,
      "", "IMPORTANT INFORMATION", ...summary.importantInformation.map((item) => `- ${item}`),
      "", "MEDICATION SCHEDULE", ...summary.medications.map((item) => `- ${item.name}: ${item.instructions}; ${item.duration}; ${item.timing}. (Source: Page ${item.source?.page ?? "not specified"})`),
      "", "FOLLOW-UP", `Date: ${formatDate(summary.followUp.date)}`, `Department: ${summary.followUp.department}`,
      ...summary.followUp.instructions.map((item) => `- ${item}`),
      "", "TESTS TO COMPLETE", ...(summary.followUp.tests?.length ? summary.followUp.tests.map((item) => `- ${item}`) : ["No tests listed in the discharge summary."]),
      `Source: Page ${summary.followUp.source?.page ?? "not specified"}`,
      "", "DISCHARGE INSTRUCTIONS", ...summary.instructions.map((item) => `- ${item}`),
      "", "Generated from the uploaded discharge summary. Check all details against the original document.",
    ].join("\n");
    const reportBlob = new Blob([report], { type: "text/plain;charset=utf-8" });
    const objectUrl = URL.createObjectURL(reportBlob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = `carebridge-${summary.patient.patientId}-discharge-details.txt`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  };

  const printReport = () => window.print();

  const submitQuestion = async (event) => {
    event.preventDefault();
    const asked = question.trim();
    if (!asked || isSending) return;
    setMessages((previous) => [...previous, { role: "user", text: asked }]);
    setQuestion("");
    setIsSending(true);
    try {
    const result = await askQuestion(summaryId, asked, language, sessionId);
      setSessionId(result.sessionId);
      setMessages((previous) => [...previous, { role: "assistant", text: result.answer, sources: Array.isArray(result.sources) ? result.sources : [], requiresHumanReview: Boolean(result.requiresHumanReview), usage: result.usage }]);
    } catch (error) {
      setMessages((previous) => [...previous, { role: "assistant", text: error.message || t.askError, sources: [] }]);
    } finally {
      setIsSending(false);
    }
  };

  const onDrop = (event) => {
    event.preventDefault();
    selectFile(event.dataTransfer.files?.[0]);
  };

  return <div className="carebridge-app" lang={language}>
    <header className="app-header">
      <a className="brand" href="/" aria-label="CareBridge-AI home"><span className="brand-heart">&#x2665;</span><span><strong>CareBridge-AI</strong><small>{t.subtitle}</small></span></a>
      <label className="language-control"><span className="globe" aria-hidden="true">&#x25CE;</span><span className="sr-only">Language</span><select value={language} onChange={(event) => setLanguage(event.target.value)}>{languages.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    </header>

    <main className="page-wrap">
      <div className="page-intro"><div><span className="eyebrow">CARE TRANSITION WORKSPACE</span><h1>{t.subtitle}</h1><p>{t.intro}</p></div><span className="secure-badge"><span aria-hidden="true">&#x2713;</span> Document workspace</span></div>

      <section className="upload-card" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
        <div className="upload-copy"><span className="upload-icon" aria-hidden="true">&#x2191;</span><div><h2>{t.upload}</h2><p>{t.uploadHint}</p></div></div>
        <div className="upload-actions"><label className="button secondary-button"><input type="file" accept="application/pdf,.pdf" onChange={(event) => { selectFile(event.target.files?.[0]); event.target.value = ""; }}/>{t.choose}</label>{file && <button className="text-button" onClick={() => { setFile(null); setSummary(null); setSourceSummary(null); setSummaryId(null); setMessages([]); }}> {t.remove}</button>}</div>
        {file && <div className="selected-file"><span className="file-icon" aria-hidden="true">PDF</span><span className="filename" title={file.name}>{file.name}</span><span className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div>}
        <div className="upload-footer"><span>{fileError || "PDF contents are processed by Gemini AI. Verify important care decisions with your clinician."}</span><button className="button primary-button" disabled={!file || isProcessing} onClick={processFile}>{isProcessing ? t.processing : t.process}</button></div>
      </section>

      {!summary ? <div className="empty-state"><span aria-hidden="true">&#x25A1;</span><p>{t.empty}</p></div> : <><div className="report-actions"><div><strong>{isTranslating ? "Translating discharge details..." : t.ready}</strong><span>{summary.patient.name} - {summary.patient.patientId}</span></div><div><button className="button secondary-button" onClick={downloadReport}>{t.downloadReport}</button><button className="button primary-button" onClick={printReport}>{t.printPdf}</button></div></div><div className="report-flow" aria-live="polite">
        <Section id="patient" title={t.patient} icon="P"><div className="overview-grid"><div><span>{t.patientName}</span><strong>{summary.patient.name}</strong></div><div><span>{t.patientId}</span><strong>{summary.patient.patientId}</strong></div><div><span>{t.ageSex}</span><strong>{summary.patient.age} / {summary.patient.gender}</strong></div><div><span>{t.hospital}</span><strong>{summary.hospital.name}</strong></div><div><span>{t.department}</span><strong>{summary.hospital.department}</strong></div><div><span>{t.admission}</span><strong>{formatDisplayDate(summary.admissionDate, language)}</strong></div><div><span>{t.discharge}</span><strong>{formatDisplayDate(summary.dischargeDate, language)}</strong></div></div><div className="plain-summary"><span>{t.summary}</span><p>{summary.summary}</p></div></Section>

        <Section id="alerts" title={t.alert} icon="!" tone="red"><ul className="content-list">{summary.importantInformation.map((item) => <li key={item}>{item}</li>)}</ul></Section>

        <Section id="medications" title={t.meds} icon="+" tone="green" source={summary.medications[0]?.source?.page} sourceLabel={t.source}><div className="table-scroll"><table className="medication-table"><thead><tr><th>{t.medicine}</th><th>{t.dosage}</th><th>{t.duration}</th><th>{t.timing}</th></tr></thead><tbody>{summary.medications.map((medication) => <tr key={medication.name}><td><strong>{medication.name}</strong></td><td>{medication.instructions}</td><td>{medication.duration}</td><td>{medication.timing}</td></tr>)}</tbody></table></div></Section>

        <Section id="follow-up" title={t.follow} icon="F" tone="purple" source={summary.followUp.source?.page} sourceLabel={t.source}><div className="follow-grid"><div><span>{t.followDate}</span><strong>{formatDisplayDate(summary.followUp.date, language)}</strong></div><div><span>{t.followDept}</span><strong>{summary.followUp.department}</strong></div></div><ul className="content-list">{summary.followUp.instructions.map((item) => <li key={item}>{item}</li>)}</ul></Section>

        <Section id="tests" title={testsText.title} icon="T" tone="blue" source={summary.followUp.source?.page} sourceLabel={t.source}><ul className="content-list">{summary.followUp.tests?.length ? summary.followUp.tests.map((item) => <li key={item}>{item}</li>) : <li>{testsText.empty}</li>}</ul></Section>

        <Section id="instructions" title={t.instructions} icon="!" tone="orange"><ol className="content-list numbered">{summary.instructions.map((item) => <li key={item}>{item}</li>)}</ol></Section>

        <Section id="ask-ai" title={t.chat} icon="AI" tone="blue"><div className="language-note">{t.languageNote}</div><div className="chat-thread" aria-live="polite">{messages.length === 0 ? <p className="chat-welcome">{t.chatWelcome}</p> : messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><span className="message-label">{message.role === "user" ? t.you : "CareBridge-AI"}</span>{message.requiresHumanReview && <strong className="human-review">{t.humanReview}</strong>}<p>{message.text}</p>{message.usage && <span className="message-usage">AI tokens: {message.usage.inputTokens + message.usage.outputTokens}; estimated cost: {message.usage.estimatedCostUsd == null ? "not configured" : `$${message.usage.estimatedCostUsd}`}</span>}{message.sources?.map((source) => <span className="message-source" key={`${source.page}-${source.section}`}>{t.source} {source.page}{source.section ? ` - ${source.section}` : ""}</span>)}</div>)}{isSending && <div className="message assistant"><span className="message-label">CareBridge-AI</span><p>{t.processing}</p></div>}</div><form className="chat-form" onSubmit={submitQuestion}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t.chatHint} aria-label={t.chatHint}/><button className="button primary-button" type="submit" disabled={!question.trim() || isSending}>{t.send}</button></form></Section>
      </div><article className="print-report"><header><h1>CareBridge-AI</h1><p>Discharge Summary Details</p></header><h2>Patient overview</h2><p><b>Patient:</b> {summary.patient.name} - <b>ID:</b> {summary.patient.patientId} - <b>Age / sex:</b> {summary.patient.age} / {summary.patient.gender}</p><p><b>Hospital:</b> {summary.hospital.name} - <b>Department:</b> {summary.hospital.department}</p><p><b>Admission:</b> {summary.admissionDate} - <b>Discharge:</b> {summary.dischargeDate}</p><h2>Summary</h2><p>{summary.summary}</p><h2>Important information</h2><ul>{summary.importantInformation.map((item) => <li key={item}>{item}</li>)}</ul><h2>Medication schedule</h2><table><thead><tr><th>Medicine</th><th>Dose &amp; instructions</th><th>Duration</th><th>Timing</th></tr></thead><tbody>{summary.medications.map((item) => <tr key={item.name}><td>{item.name}</td><td>{item.instructions}</td><td>{item.duration}</td><td>{item.timing}</td></tr>)}</tbody></table><h2>Follow-up</h2><p>{summary.followUp.date} - {summary.followUp.department}</p><ul>{summary.followUp.instructions.map((item) => <li key={item}>{item}</li>)}</ul><h2>Tests to Complete</h2><ul>{summary.followUp.tests?.length ? summary.followUp.tests.map((item) => <li key={item}>{item}</li>) : <li>No tests are listed in the discharge summary.</li>}</ul><p>Source: Page {summary.followUp.source?.page ?? "not specified"}</p><h2>Discharge instructions</h2><ul>{summary.instructions.map((item) => <li key={item}>{item}</li>)}</ul><p className="print-note">AI-generated explanation of the uploaded discharge document.</p></article></>}
      <footer className="page-footer">CareBridge-AI - Explanations are based on your uploaded discharge summary.</footer>
    </main>
  </div>;
}

export default App;
