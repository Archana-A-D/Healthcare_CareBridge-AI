import { useState } from "react";
import dischargeSummary from "./mocks/dischargeSummary.json";
import { askQuestion, uploadDischargeSummary } from "./services/mockApi";
import "./App.css";

const copy = {
  en: { subtitle: "Discharge Summary Explainer", intro: "Understand discharge information clearly, in one place.", upload: "Upload a discharge summary", uploadHint: "Choose a PDF or drag it here", choose: "Choose PDF", process: "Process document", processing: "Processing…", remove: "Remove file", downloadReport: "Download details (.txt)", printPdf: "Print / Save as PDF", ready: "Discharge details are ready", patient: "Patient overview", alert: "Important information", meds: "Medication schedule", medicine: "Medicine", dosage: "Dose & instructions", duration: "Duration", timing: "Timing", follow: "Follow-up details", instructions: "Discharge instructions", missing: "Missing information", chat: "Ask about this document", chatHint: "Ask a question about this discharge summary…", send: "Send", demo: "Demo mode: the uploaded PDF is not analyzed yet. The sections below use sample discharge data.", languageNote: "Medical details remain in the source document's language.", empty: "Select and process a PDF to show the discharge details here.", patientName: "Patient name", patientId: "Patient ID", ageSex: "Age / sex", hospital: "Hospital", department: "Department", admission: "Admission date", discharge: "Discharge date", summary: "Summary", followDate: "Follow-up date", followDept: "Department", you: "You", chatWelcome: "Ask about medications, follow-up, or instructions in this summary.", source: "Source: Page", answer: "Based on the sample discharge summary", uploadError: "Please select a PDF file.", askError: "Could not get an answer. Please try again." },
  ml: { subtitle: "ഡിസ്ചാർജ് സംഗ്രഹ വിശദീകരണം", intro: "ഡിസ്ചാർജ് വിവരങ്ങൾ വ്യക്തമായി ഒരിടത്ത് മനസ്സിലാക്കുക.", upload: "ഡിസ്ചാർജ് സംഗ്രഹം അപ്‌ലോഡ് ചെയ്യുക", uploadHint: "PDF തിരഞ്ഞെടുക്കുക അല്ലെങ്കിൽ ഇവിടെ ഇടുക", choose: "PDF തിരഞ്ഞെടുക്കുക", process: "രേഖ പ്രോസസ്സ് ചെയ്യുക", processing: "പ്രോസസ്സ് ചെയ്യുന്നു…", remove: "ഫയൽ നീക്കം ചെയ്യുക", downloadReport: "വിവരങ്ങൾ ഡൗൺലോഡ് ചെയ്യുക (.txt)", printPdf: "പ്രിന്റ് / PDF ആയി സേവ് ചെയ്യുക", ready: "ഡിസ്ചാർജ് വിവരങ്ങൾ തയ്യാറാണ്", patient: "രോഗിയുടെ വിവരങ്ങൾ", alert: "പ്രധാന വിവരങ്ങൾ", meds: "മരുന്നുകളുടെ പട്ടിക", medicine: "മരുന്ന്", dosage: "ഡോസ്, നിർദ്ദേശങ്ങൾ", duration: "കാലാവധി", timing: "സമയം", follow: "തുടർപരിശോധന വിവരങ്ങൾ", instructions: "ഡിസ്ചാർജ് നിർദ്ദേശങ്ങൾ", missing: "ലഭ്യമല്ലാത്ത വിവരങ്ങൾ", chat: "ഈ രേഖയെക്കുറിച്ച് ചോദിക്കുക", chatHint: "ഈ ഡിസ്ചാർജ് സംഗ്രഹത്തെക്കുറിച്ച് ചോദിക്കുക…", send: "അയയ്ക്കുക", demo: "ഡെമോ: അപ്‌ലോഡ് ചെയ്ത PDF ഇപ്പോൾ വിശകലനം ചെയ്യുന്നില്ല. താഴെയുള്ള ഭാഗങ്ങൾ സാമ്പിൾ വിവരങ്ങളാണ്.", languageNote: "വൈദ്യ വിവരങ്ങൾ ഉറവിട രേഖയുടെ ഭാഷയിൽ തുടരും.", empty: "ഡിസ്ചാർജ് വിവരങ്ങൾ കാണാൻ ഒരു PDF തിരഞ്ഞെടുക്കുക.", patientName: "രോഗിയുടെ പേര്", patientId: "രോഗി ഐഡി", ageSex: "പ്രായം / ലിംഗം", hospital: "ആശുപത്രി", department: "വിഭാഗം", admission: "പ്രവേശന തീയതി", discharge: "ഡിസ്ചാർജ് തീയതി", summary: "സംഗ്രഹം", followDate: "തുടർപരിശോധന തീയതി", followDept: "വിഭാഗം", you: "നിങ്ങൾ", chatWelcome: "മരുന്നുകൾ, തുടർപരിശോധന, അല്ലെങ്കിൽ നിർദ്ദേശങ്ങൾ ചോദിക്കുക.", source: "ഉറവിടം: പേജ്", answer: "സാമ്പിൾ ഡിസ്ചാർജ് സംഗ്രഹത്തെ അടിസ്ഥാനമാക്കി", uploadError: "ഒരു PDF ഫയൽ തിരഞ്ഞെടുക്കുക.", askError: "ഉത്തരം ലഭിച്ചില്ല. വീണ്ടും ശ്രമിക്കുക." },
  ta: { subtitle: "வெளியேற்றச் சுருக்க விளக்கி", intro: "வெளியேற்றத் தகவல்களைத் தெளிவாக ஒரே இடத்தில் அறியுங்கள்.", upload: "வெளியேற்றச் சுருக்கத்தைப் பதிவேற்றவும்", uploadHint: "PDF-ஐ தேர்ந்தெடுக்கவும் அல்லது இங்கே விடவும்", choose: "PDF தேர்வு", process: "ஆவணத்தைச் செயலாக்கு", processing: "செயலாக்கப்படுகிறது…", remove: "கோப்பை நீக்கு", downloadReport: "விவரங்களைப் பதிவிறக்கு (.txt)", printPdf: "அச்சிடு / PDF ஆக சேமி", ready: "வெளியேற்ற விவரங்கள் தயார்", patient: "நோயாளி விவரங்கள்", alert: "முக்கிய தகவல்", meds: "மருந்து அட்டவணை", medicine: "மருந்து", dosage: "அளவு மற்றும் வழிமுறைகள்", duration: "காலம்", timing: "நேரம்", follow: "தொடர் சிகிச்சை விவரங்கள்", instructions: "வெளியேற்ற வழிமுறைகள்", missing: "கிடைக்காத தகவல்", chat: "இந்த ஆவணத்தைப் பற்றி கேளுங்கள்", chatHint: "இந்த வெளியேற்றச் சுருக்கத்தைப் பற்றி கேளுங்கள்…", send: "அனுப்பு", demo: "டெமோ: பதிவேற்றிய PDF இன்னும் பகுப்பாய்வு செய்யப்படவில்லை. கீழே உள்ளவை மாதிரி தகவல்கள்.", languageNote: "மருத்துவ விவரங்கள் மூல ஆவணத்தின் மொழியிலேயே இருக்கும்.", empty: "விவரங்களைக் காண PDF-ஐத் தேர்ந்தெடுத்து செயலாக்கவும்.", patientName: "நோயாளியின் பெயர்", patientId: "நோயாளி எண்", ageSex: "வயது / பாலினம்", hospital: "மருத்துவமனை", department: "துறை", admission: "சேர்க்கை தேதி", discharge: "வெளியேற்ற தேதி", summary: "சுருக்கம்", followDate: "தொடர் சிகிச்சை தேதி", followDept: "துறை", you: "நீங்கள்", chatWelcome: "மருந்துகள், தொடர் சிகிச்சை அல்லது வழிமுறைகள் பற்றி கேளுங்கள்.", source: "மூலம்: பக்கம்", answer: "மாதிரி வெளியேற்றச் சுருக்கத்தின் அடிப்படையில்", uploadError: "PDF கோப்பைத் தேர்ந்தெடுக்கவும்.", askError: "பதில் கிடைக்கவில்லை. மீண்டும் முயற்சிக்கவும்." },
  hi: { subtitle: "डिस्चार्ज सारांश समझें", intro: "डिस्चार्ज की जानकारी एक जगह, सरल तरीके से समझें।", upload: "डिस्चार्ज सारांश अपलोड करें", uploadHint: "PDF चुनें या यहाँ छोड़ें", choose: "PDF चुनें", process: "दस्तावेज़ प्रोसेस करें", processing: "प्रोसेस हो रहा है…", remove: "फ़ाइल हटाएँ", downloadReport: "जानकारी डाउनलोड करें (.txt)", printPdf: "प्रिंट / PDF के रूप में सेव करें", ready: "डिस्चार्ज विवरण तैयार है", patient: "मरीज़ की जानकारी", alert: "महत्वपूर्ण जानकारी", meds: "दवाओं का विवरण", medicine: "दवा", dosage: "खुराक और निर्देश", duration: "अवधि", timing: "समय", follow: "फ़ॉलो-अप विवरण", instructions: "डिस्चार्ज निर्देश", missing: "अनुपलब्ध जानकारी", chat: "इस दस्तावेज़ के बारे में पूछें", chatHint: "इस डिस्चार्ज सारांश के बारे में सवाल पूछें…", send: "भेजें", demo: "डेमो: अपलोड की गई PDF का अभी विश्लेषण नहीं होता। नीचे नमूना जानकारी दिखाई गई है।", languageNote: "चिकित्सीय विवरण मूल दस्तावेज़ की भाषा में रहेंगे।", empty: "डिस्चार्ज विवरण देखने के लिए PDF चुनकर प्रोसेस करें।", patientName: "मरीज़ का नाम", patientId: "मरीज़ आईडी", ageSex: "उम्र / लिंग", hospital: "अस्पताल", department: "विभाग", admission: "भर्ती की तारीख", discharge: "डिस्चार्ज की तारीख", summary: "सारांश", followDate: "फ़ॉलो-अप की तारीख", followDept: "विभाग", you: "आप", chatWelcome: "दवाओं, फ़ॉलो-अप या निर्देशों के बारे में पूछें।", source: "स्रोत: पृष्ठ", answer: "नमूना डिस्चार्ज सारांश के आधार पर", uploadError: "कृपया PDF फ़ाइल चुनें।", askError: "उत्तर नहीं मिल सका। फिर से कोशिश करें।" },
};

const languages = [["en", "English"], ["ml", "മലയാളം"], ["ta", "தமிழ்"], ["hi", "हिन्दी"]];
const testCopy = {
  en: { title: "Tests to Complete", empty: "No tests are listed in the discharge summary." },
  ml: { title: "ചെയ്യേണ്ട പരിശോധനകൾ", empty: "ഡിസ്ചാർജ് സംഗ്രഹത്തിൽ പരിശോധനകൾ നൽകിയിട്ടില്ല." },
  ta: { title: "செய்ய வேண்டிய பரிசோதனைகள்", empty: "வெளியேற்றச் சுருக்கத்தில் பரிசோதனைகள் குறிப்பிடப்படவில்லை." },
  hi: { title: "कराई जाने वाली जाँचें", empty: "डिस्चार्ज सारांश में कोई जाँच नहीं दी गई है।" },
};

function Section({ id, title, icon, children, tone = "blue", source, sourceLabel = "Source: Page" }) {
  return <section className={`flow-card ${tone}`} id={id}><div className="flow-card-heading"><span className="section-icon" aria-hidden="true">{icon}</span><h2>{title}</h2></div><div className="flow-card-body">{children}</div>{source && <div className="citation">{sourceLabel} {source}</div>}</section>;
}

function App() {
  const [language, setLanguage] = useState("en");
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const t = copy[language];
  const testsText = testCopy[language];

  const useSelectedFile = (selectedFile) => {
    setFileError("");
    if (!selectedFile) return;
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setFileError(t.uploadError);
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setSummary(null);
    setMessages([]);
  };

  const processFile = async () => {
    if (!file) { setFileError(t.uploadError); return; }
    setIsProcessing(true);
    setFileError("");
    try {
      await uploadDischargeSummary(file);
      setSummary(dischargeSummary);
    } catch {
      setFileError("Upload failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadReport = () => {
    if (!summary) return;
    const formatDate = (date) => new Date(`${date}T00:00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
    const report = [
      "CareBridge-AI — Discharge Summary Details",
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
      "", "MISSING INFORMATION", ...summary.missingInformation.map((item) => `- ${item}`),
      "", "Demo report generated from the sample discharge dataset.",
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
      const result = await askQuestion(asked);
      setMessages((previous) => [...previous, { role: "assistant", text: result.answer, sources: result.sources ?? [] }]);
    } catch {
      setMessages((previous) => [...previous, { role: "assistant", text: t.askError, sources: [] }]);
    } finally {
      setIsSending(false);
    }
  };

  const onDrop = (event) => {
    event.preventDefault();
    useSelectedFile(event.dataTransfer.files?.[0]);
  };

  return <div className="carebridge-app" lang={language}>
    <header className="app-header">
      <a className="brand" href="/" aria-label="CareBridge-AI home"><span className="brand-heart">♥</span><span><strong>CareBridge-AI</strong><small>{t.subtitle}</small></span></a>
      <label className="language-control"><span className="globe" aria-hidden="true">◎</span><span className="sr-only">Language</span><select value={language} onChange={(event) => setLanguage(event.target.value)}>{languages.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    </header>

    <main className="page-wrap">
      <div className="page-intro"><div><span className="eyebrow">CARE TRANSITION WORKSPACE</span><h1>{t.subtitle}</h1><p>{t.intro}</p></div><span className="secure-badge"><span aria-hidden="true">✓</span> Document workspace</span></div>

      <section className="upload-card" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
        <div className="upload-copy"><span className="upload-icon" aria-hidden="true">↑</span><div><h2>{t.upload}</h2><p>{t.uploadHint}</p></div></div>
        <div className="upload-actions"><label className="button secondary-button"><input type="file" accept="application/pdf,.pdf" onChange={(event) => { useSelectedFile(event.target.files?.[0]); event.target.value = ""; }}/>{t.choose}</label>{file && <button className="text-button" onClick={() => { setFile(null); setSummary(null); setMessages([]); }}> {t.remove}</button>}</div>
        {file && <div className="selected-file"><span className="file-icon" aria-hidden="true">PDF</span><span className="filename" title={file.name}>{file.name}</span><span className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div>}
        <div className="upload-footer"><span>{fileError || t.demo}</span><button className="button primary-button" disabled={!file || isProcessing} onClick={processFile}>{isProcessing ? t.processing : t.process}</button></div>
      </section>

      {!summary ? <div className="empty-state"><span aria-hidden="true">▧</span><p>{t.empty}</p></div> : <><div className="report-actions"><div><strong>{t.ready}</strong><span>{summary.patient.name} · {summary.patient.patientId}</span></div><div><button className="button secondary-button" onClick={downloadReport}>↓  {t.downloadReport}</button><button className="button primary-button" onClick={printReport}>▤  {t.printPdf}</button></div></div><div className="report-flow" aria-live="polite">
        <Section id="patient" title={t.patient} icon="●"><div className="overview-grid"><div><span>{t.patientName}</span><strong>{summary.patient.name}</strong></div><div><span>{t.patientId}</span><strong>{summary.patient.patientId}</strong></div><div><span>{t.ageSex}</span><strong>{summary.patient.age} / {summary.patient.gender}</strong></div><div><span>{t.hospital}</span><strong>{summary.hospital.name}</strong></div><div><span>{t.department}</span><strong>{summary.hospital.department}</strong></div><div><span>{t.admission}</span><strong>{new Date(`${summary.admissionDate}T00:00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}</strong></div><div><span>{t.discharge}</span><strong>{new Date(`${summary.dischargeDate}T00:00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}</strong></div></div><div className="plain-summary"><span>{t.summary}</span><p>{summary.summary}</p></div></Section>

        <Section id="alerts" title={t.alert} icon="!" tone="red"><ul className="content-list">{summary.importantInformation.map((item) => <li key={item}>{item}</li>)}</ul></Section>

        <Section id="medications" title={t.meds} icon="＋" tone="green" source={summary.medications[0]?.source?.page} sourceLabel={t.source}><div className="table-scroll"><table className="medication-table"><thead><tr><th>{t.medicine}</th><th>{t.dosage}</th><th>{t.duration}</th><th>{t.timing}</th></tr></thead><tbody>{summary.medications.map((medication) => <tr key={medication.name}><td><strong>{medication.name}</strong></td><td>{medication.instructions}</td><td>{medication.duration}</td><td>{medication.timing}</td></tr>)}</tbody></table></div></Section>

        <Section id="follow-up" title={t.follow} icon="◷" tone="purple" source={summary.followUp.source?.page} sourceLabel={t.source}><div className="follow-grid"><div><span>{t.followDate}</span><strong>{new Date(`${summary.followUp.date}T00:00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" })}</strong></div><div><span>{t.followDept}</span><strong>{summary.followUp.department}</strong></div></div><ul className="content-list">{summary.followUp.instructions.map((item) => <li key={item}>{item}</li>)}</ul></Section>

        <Section id="tests" title={testsText.title} icon="✓" tone="blue" source={summary.followUp.source?.page} sourceLabel={t.source}><ul className="content-list">{summary.followUp.tests?.length ? summary.followUp.tests.map((item) => <li key={item}>{item}</li>) : <li>{testsText.empty}</li>}</ul></Section>

        <Section id="instructions" title={t.instructions} icon="☷" tone="orange"><ol className="content-list numbered">{summary.instructions.map((item) => <li key={item}>{item}</li>)}</ol></Section>

        <Section id="missing" title={t.missing} icon="i" tone="amber"><ul className="content-list">{summary.missingInformation.length ? summary.missingInformation.map((item) => <li key={item}>{item}</li>) : <li>None listed.</li>}</ul></Section>

        <Section id="ask-ai" title={t.chat} icon="✦" tone="blue"><div className="language-note">{t.languageNote}</div><div className="chat-thread" aria-live="polite">{messages.length === 0 ? <p className="chat-welcome">{t.chatWelcome}</p> : messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><span className="message-label">{message.role === "user" ? t.you : "CareBridge-AI"}</span><p>{message.text}</p>{message.sources?.map((source) => <span className="message-source" key={`${source.page}-${source.section}`}>{t.source} {source.page}{source.section ? ` · ${source.section}` : ""}</span>)}</div>)}{isSending && <div className="message assistant"><span className="message-label">CareBridge-AI</span><p>{t.processing}</p></div>}</div><form className="chat-form" onSubmit={submitQuestion}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t.chatHint} aria-label={t.chatHint}/><button className="button primary-button" type="submit" disabled={!question.trim() || isSending}>{t.send} <span aria-hidden="true">➤</span></button></form></Section>
      </div><article className="print-report"><header><h1>CareBridge-AI</h1><p>Discharge Summary Details</p></header><h2>Patient overview</h2><p><b>Patient:</b> {summary.patient.name} · <b>ID:</b> {summary.patient.patientId} · <b>Age / sex:</b> {summary.patient.age} / {summary.patient.gender}</p><p><b>Hospital:</b> {summary.hospital.name} · <b>Department:</b> {summary.hospital.department}</p><p><b>Admission:</b> {summary.admissionDate} · <b>Discharge:</b> {summary.dischargeDate}</p><h2>Summary</h2><p>{summary.summary}</p><h2>Important information</h2><ul>{summary.importantInformation.map((item) => <li key={item}>{item}</li>)}</ul><h2>Medication schedule</h2><table><thead><tr><th>Medicine</th><th>Dose &amp; instructions</th><th>Duration</th><th>Timing</th></tr></thead><tbody>{summary.medications.map((item) => <tr key={item.name}><td>{item.name}</td><td>{item.instructions}</td><td>{item.duration}</td><td>{item.timing}</td></tr>)}</tbody></table><h2>Follow-up</h2><p>{summary.followUp.date} · {summary.followUp.department}</p><ul>{summary.followUp.instructions.map((item) => <li key={item}>{item}</li>)}</ul><h2>Tests to Complete</h2><ul>{summary.followUp.tests?.length ? summary.followUp.tests.map((item) => <li key={item}>{item}</li>) : <li>No tests are listed in the discharge summary.</li>}</ul><p>Source: Page {summary.followUp.source?.page ?? "not specified"}</p><h2>Discharge instructions</h2><ul>{summary.instructions.map((item) => <li key={item}>{item}</li>)}</ul><h2>Missing information</h2><ul>{summary.missingInformation.map((item) => <li key={item}>{item}</li>)}</ul><p className="print-note">Generated from the CareBridge-AI sample discharge dataset.</p></article></>}
      <footer className="page-footer">CareBridge-AI · Discharge information is shown from the selected sample data.</footer>
    </main>
  </div>;
}

export default App;
