// ═══════════════════════════════════════════════════════════════════════════
//  GOOGLE APPS SCRIPT — paste this in script.google.com
//  Attach to your BIM Training Google Sheet
//  Set trigger: onEdit → Spreadsheet → On edit
// ═══════════════════════════════════════════════════════════════════════════

const WEBHOOK_URL = 'https://YOUR-APP.railway.app';  // ← Your Railway URL
const API_KEY     = 'bim_training_webhook_secret_2026'; // ← Same as VERIFY_TOKEN

function onEdit(e) {
  const sheet = e.range.getSheet();
  const col   = e.range.getColumn();
  const val   = e.value;

  if (sheet.getName() !== 'Students') return;

  // Col 12 = Status
  if (col === 12) {
    const row  = e.range.getRow();
    const data = getStudentRow(sheet, row);

    if (val === 'Payment Confirmed') sendPaymentConfirmed(data);
    if (val === 'Completed')         sendCertificate(data);
  }
}

function getStudentRow(sheet, row) {
  const r = sheet.getRange(row, 1, 1, 21).getValues()[0];
  return {
    studentId:   r[0],  name:      r[1],  phone: r[2],
    email:       r[3],  course:    r[9],  batchDate: String(r[10]),
    attendance:  r[18], projectDone: r[19],
  };
}

function sendPaymentConfirmed(data) {
  const phone = String(data.phone).replace('+','').replace(/\s/g,'');
  callWebhook('/api/confirm-payment', {
    phone:      phone,
    name:       data.name,
    email:      data.email,
    course:     data.course,
    student_id: data.studentId,
    batch_date: data.batchDate,
  });
}

function sendCertificate(data) {
  const phone = String(data.phone).replace('+','').replace(/\s/g,'');
  callWebhook('/api/send-certificate', {
    phone:      phone,
    name:       data.name,
    email:      data.email,
    course:     data.course,
    student_id: data.studentId,
  });
}

function scheduleNextSession() {
  // Edit these values and run manually before each class
  callWebhook('/api/schedule-reminder', {
    session_datetime: '2026-03-15T10:00:00+05:30',
    zoom_link:        'https://zoom.us/j/YOUR_MEETING_ID',
    course_name:      'Architecture BIM Training',
  });
}

function callWebhook(path, payload) {
  try {
    const res = UrlFetchApp.fetch(WEBHOOK_URL + path, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': API_KEY },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
    });
    Logger.log(path + ' → ' + res.getContentText());
  } catch(e) {
    Logger.log('Error calling ' + path + ': ' + e.toString());
  }
}
