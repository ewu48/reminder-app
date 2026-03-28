import { api } from "./api.js";

export class ReminderForm {
  #form;
  #toast;
  #onSuccess;
  #submitBtn;
  #errorEl;

  constructor(formEl, toast, onSuccess) {
    this.#form = formEl;
    this.#toast = toast;
    this.#onSuccess = onSuccess;
    this.#submitBtn = formEl.querySelector('[type="submit"]');
    this.#errorEl = formEl.querySelector(".form-error");

    this.#setDefaultTime();
    formEl.addEventListener("submit", e => this.#handleSubmit(e));
  }

  // ── Private ───────────────────────────────────────────────────────────────

  #setDefaultTime() {
    const dt = new Date(Date.now() + 60 * 60 * 1000);
    dt.setSeconds(0, 0);
    this.#form.elements.eventTime.value = dt.toISOString().slice(0, 16);
  }

  async #handleSubmit(e) {
    e.preventDefault();
    this.#clearError();
    this.#setLoading(true);

    const { eventName, eventTime, alertAmount, alertUnit } = this.#form.elements;

    try {
      await api.reminders.create({
        event_name:    eventName.value.trim(),
        event_time:    eventTime.value,
        alert_minutes: Number(alertAmount.value) * Number(alertUnit.value),
      });
      this.#form.reset();
      this.#setDefaultTime();
      this.#toast.success("Reminder added!");
      this.#onSuccess();
    } catch (err) {
      this.#showError(err.message);
    } finally {
      this.#setLoading(false);
    }
  }

  #setLoading(loading) {
    this.#submitBtn.disabled = loading;
    this.#submitBtn.textContent = loading ? "Adding…" : "Add Reminder";
  }

  #showError(msg) {
    this.#errorEl.textContent = msg;
    this.#errorEl.hidden = false;
  }

  #clearError() {
    this.#errorEl.textContent = "";
    this.#errorEl.hidden = true;
  }
}
