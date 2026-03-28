export class Toast {
  #el;
  #timer = null;

  constructor(el) {
    this.#el = el;
  }

  show(message, variant = "success") {
    clearTimeout(this.#timer);
    this.#el.textContent = message;
    this.#el.dataset.variant = variant;
    this.#el.classList.add("toast--visible");
    this.#timer = setTimeout(() => this.#el.classList.remove("toast--visible"), 3000);
  }

  success(msg) { this.show(msg, "success"); }
  error(msg)   { this.show(msg, "error"); }
}
