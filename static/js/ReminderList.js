import { api } from "./api.js";
import { formatDateTime, timeUntil } from "./utils.js";

export class ReminderList {
  #container;
  #toast;
  #items = [];

  constructor(containerEl, toast) {
    this.#container = containerEl;
    this.#toast = toast;

    // Single delegated listener — avoids attaching/detaching on every render
    this.#container.addEventListener("click", e => {
      const btn = e.target.closest("[data-delete-id]");
      if (btn) this.#handleDelete(btn.dataset.deleteId);
    });
  }

  async refresh() {
    this.#container.dataset.loading = "true";
    try {
      this.#items = await api.reminders.list();
      this.#render();
    } catch (err) {
      this.#toast.error(err.message);
    } finally {
      delete this.#container.dataset.loading;
    }
  }

  // ── Private ───────────────────────────────────────────────────────────────

  #render() {
    if (!this.#items.length) {
      const p = document.createElement("p");
      p.className = "reminder-list__empty";
      p.textContent = "No upcoming reminders.";
      this.#container.replaceChildren(p);
      return;
    }
    this.#container.replaceChildren(...this.#items.map(r => this.#buildItem(r)));
  }

  #buildItem(r) {
    const until = timeUntil(r.alert_time);

    const icon = el("span", { className: "reminder-item__icon", textContent: "📅" });

    const name = el("div", { className: "reminder-item__name", textContent: r.event_name });
    const eventTime = el("div", {
      className: "reminder-item__event-time",
      textContent: `Event: ${formatDateTime(r.event_time)}`,
    });
    const alertTime = el("div", {
      className: "reminder-item__alert-time",
      textContent: `🔔 Alert: ${formatDateTime(r.alert_time)}${until ? ` · in ${until}` : ""}`,
    });
    const info = el("div", { className: "reminder-item__info" });
    info.append(name, eventTime, alertTime);

    const deleteBtn = el("button", {
      className: "btn btn--danger",
      textContent: "Delete",
      dataset: { deleteId: r.id },
    });

    const article = el("article", { className: "reminder-item", dataset: { id: r.id } });
    article.append(icon, info, deleteBtn);
    return article;
  }

  async #handleDelete(id) {
    if (!confirm("Delete this reminder?")) return;
    try {
      await api.reminders.delete(id);
      this.#items = this.#items.filter(r => r.id !== id);
      this.#render();
      this.#toast.success("Reminder deleted");
    } catch (err) {
      this.#toast.error(err.message);
    }
  }
}

// ── Helper ──────────────────────────────────────────────────────────────────

function el(tag, props = {}) {
  const node = document.createElement(tag);
  const { dataset, ...rest } = props;
  Object.assign(node, rest);
  if (dataset) Object.assign(node.dataset, dataset);
  return node;
}
