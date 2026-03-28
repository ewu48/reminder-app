import { Toast } from "./Toast.js";
import { ReminderList } from "./ReminderList.js";
import { ReminderForm } from "./ReminderForm.js";

const toast = new Toast(document.getElementById("toast"));
const list  = new ReminderList(document.getElementById("reminderList"), toast);

new ReminderForm(
  document.getElementById("reminderForm"),
  toast,
  () => list.refresh(),
);

list.refresh();
setInterval(() => list.refresh(), 60_000);
