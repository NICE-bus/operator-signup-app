/**
 * Automatically generates a copy of a template sheet for every day in given range in Apps Script.
 */
function generateDailySheets() {
  // 1. SETTINGS: Replace these with your actual IDs
  var templateId = 'YOUR_TEMPLATE_SHEET_ID'; // Found in the sheet URL
  var folderId = 'YOUR_TARGET_FOLDER_ID';     // Found in the Drive folder URL
  
  var folder = DriveApp.getFolderById(folderId);
  var templateFile = DriveApp.getFileById(templateId);
  
  // 2. DEFINE THE RANGE
  // Months are 0-indexed in JavaScript (0=Jan, 1=Feb, 11=Dec)
  var startDate = new Date(2026, 1, 17); 
  var endDate = new Date(2026, 11, 31);
  
  var currentDate = new Date(startDate);
  
  // 3. LOOP THROUGH DATES
  while (currentDate <= endDate) {
    var formattedDate = Utilities.formatDate(currentDate, Session.getScriptTimeZone(), "yyyy-MM-dd");
    
    console.log("Creating sheet for: " + formattedDate);
    
    // Make a copy of the entire file (this preserves all tabs and headers)
    templateFile.makeCopy(formattedDate, folder);
    
    // Increment the day by 1
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  console.log("Process complete!");
}