/**
 * GNN Logistics contact form -> Google Sheets
 *
 * Setup:
 * 1. Create a Google Sheet with headers:
 *    Timestamp | Name | Email | Phone | Service | Message
 * 2. Extensions -> Apps Script -> paste this file
 * 3. Set SHEET_NAME and SPREADSHEET_ID
 * 4. Deploy -> New deployment -> Web app
 *    Execute as: Me
 *    Who has access: Anyone
 * 5. Copy deployment URL into client/.env as VITE_GOOGLE_SCRIPT_URL
 */

const SPREADSHEET_ID = "YOUR_SPREADSHEET_ID";
const SHEET_NAME = "Inquiries";

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
      JSON.stringify({ success: true })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, error: error.message })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
