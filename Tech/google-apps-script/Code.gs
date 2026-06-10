/**
 * GNN Logistics contact form -> Google Sheets
 *
 * Deploy as Web App (Execute as: Me, Access: Anyone)
 * Then set GOOGLE_SCRIPT_URL in Vercel env vars.
 */

const SPREADSHEET_ID = "YOUR_SPREADSHEET_ID";
const SHEET_NAME = "Inquiries";

function doOptions() {
  return ContentService.createTextOutput("")
    .setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);

    sheet.appendRow([
      data.submittedAt || new Date().toISOString(),
      data.name || "",
      data.email || "",
      data.phone || "",
      data.service || "",
      data.message || "",
    ]);

    return ContentService.createTextOutput(
      JSON.stringify({ success: true, message: "Inquiry saved to Google Sheets." })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, error: error.message })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function setupSheet() {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = spreadsheet.getSheetByName(SHEET_NAME);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(SHEET_NAME);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Timestamp", "Name", "Email", "Phone", "Service", "Message"]);
  }
}
