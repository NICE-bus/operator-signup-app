/**
 * Generates a copy of a updated template for every day from Feb 17 to Dec 31, 2026.
 */
function redoDailySheets() {
  // 1. SETTINGS
  var templateId = '19ybYPVsoqNkQppol8pWJ9CoIKMZgJ_1S7RdNiAOON4s'; // The ID of your UPDATED template
  var folderId = '1dYd5Lk0O2x8-huNXfslRHpjWVEMu3L2q';     // The ID of the folder (make sure it's empty!)
  
  // 2. DEFINE THE RANGE
  // Months are 0-indexed in JavaScript (0=Jan, 1=Feb, 11=Dec)
  var startDate = new Date(2026, 2, 2);   // Mar 2, 2026
  var endDate = new Date(2026, 11, 31);   // Dec 31, 2026
  
  var folder = DriveApp.getFolderById(folderId);
  var templateFile = DriveApp.getFileById(templateId);
  var currentDate = new Date(startDate);
  
  // 3. THE LOOP
  while (currentDate <= endDate) {
    var formattedDate = Utilities.formatDate(currentDate, Session.getScriptTimeZone(), "yyyy-MM-dd");
    
    try {
      console.log("Creating: " + formattedDate);
      templateFile.makeCopy(formattedDate, folder);
    } catch (e) {
      console.log("Error on " + formattedDate + ": " + e.toString());
      break; // Stops the script if something goes wrong
    }
    
    // Move to the next day
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  console.log("Batch complete. Check your folder!");
}