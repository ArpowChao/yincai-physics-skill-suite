const SPREADSHEET_ID = '12UqQgG3GNxepKRNLeKjW5T1NvQEHqg2gMObu6IR1ZjU';
const SHEET_NAME = '讀音候選';
const HEADERS = ['提交時間', '原稿詞語', '配音寫法', '使用語境', '來源頁面', '狀態', '維護備註'];

function setupCandidateSheet() {
  const sheet = getOrCreateSheet_();
  ensureHeader_(sheet);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setFontWeight('bold')
    .setBackground('#10213f')
    .setFontColor('#ffffff');
  sheet.autoResizeColumns(1, HEADERS.length);
}

function doGet() {
  return jsonOutput_({ ok: true, service: 'tts-pronunciation-candidate-inbox' });
}

function doPost(event) {
  try {
    const parameters = event && event.parameter ? event.parameter : {};
    if (parameters.website) {
      return jsonOutput_({ ok: true });
    }

    const original = requiredText_(parameters.original, '原稿詞語', 80);
    const spoken = requiredText_(parameters.spoken, '配音寫法', 80);
    const context = optionalText_(parameters.context, 500);
    const sourceUrl = optionalText_(parameters.source_url, 300);

    const lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      const sheet = getOrCreateSheet_();
      ensureHeader_(sheet);
      sheet.appendRow([
        new Date(),
        safeCell_(original),
        safeCell_(spoken),
        safeCell_(context),
        safeCell_(sourceUrl),
        '待確認',
        '',
      ]);
      SpreadsheetApp.flush();
    } finally {
      lock.releaseLock();
    }
    return jsonOutput_({ ok: true });
  } catch (error) {
    return jsonOutput_({ ok: false, error: String(error.message || error) });
  }
}

function getOrCreateSheet_() {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  return spreadsheet.getSheetByName(SHEET_NAME) || spreadsheet.insertSheet(SHEET_NAME);
}

function ensureHeader_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
  }
}

function requiredText_(value, label, maxLength) {
  const text = String(value || '').trim();
  if (!text) throw new Error(`${label}不可空白。`);
  if (text.length > maxLength) throw new Error(`${label}超過 ${maxLength} 字。`);
  return text;
}

function optionalText_(value, maxLength) {
  return String(value || '').trim().slice(0, maxLength);
}

function safeCell_(value) {
  const text = String(value || '');
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

function jsonOutput_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
