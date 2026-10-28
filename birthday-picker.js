/*  <birthday-picker> — a self-contained birthday selector with an age avatar.
 *
 *  Usage:
 *    <script src="birthday-picker.js"></script>
 *    <birthday-picker name="birthday"></birthday-picker>
 *
 *  Attributes
 *    name        form field name (submits "YYYY-MM-DD" when inside a <form>)
 *    value       initial value, "YYYY-MM-DD"
 *    avatars     folder holding age-000.svg … age-140.svg (default: ./avatars/ next to this script)
 *    min-year    oldest selectable year   (default: current year - 140)
 *    max-year    newest selectable year   (default: current year)
 *    hide-age    omit the "Age N" caption under the avatar
 *
 *  Properties:  value, year, month, day, age      Event:  "change" (detail: {year, month, day, age, value})
 *
 *  The year control is a custom listbox (not a native <select>) so the avatar can preview
 *  the age while you hover over or arrow through the years before committing a choice.
 */
(function () {
  "use strict";

  // build.py replaces the null below with an array of 141 data: URIs to make the single-file bundle.
  const INLINE_AVATARS = /*__INLINE_AVATARS__*/ null;

  const scriptSrc = document.currentScript && document.currentScript.src;
  const DEFAULT_AVATARS = scriptSrc ? new URL("avatars/", scriptSrc).href : "avatars/";
  const MAX_AGE = 140;
  const MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

  const STYLE = `
    :host {
      --bp-avatar-size: 120px;
      --bp-gap: 16px;
      --bp-font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      --bp-text: #1f2328;
      --bp-muted: #6b7280;
      --bp-border: #d0d5dc;
      --bp-bg: #fff;
      --bp-accent: #3f83f8;
      --bp-highlight: #e8f0fe;
      --bp-radius: 8px;
      display: inline-flex;
      align-items: center;
      gap: var(--bp-gap);
      font-family: var(--bp-font);
      color: var(--bp-text);
      box-sizing: border-box;
    }
    :host([hidden]) { display: none; }
    *, *::before, *::after { box-sizing: border-box; }
    .avatar {
      position: relative;
      width: var(--bp-avatar-size);
      height: var(--bp-avatar-size);
      flex: 0 0 auto;
      border-radius: 50%;
      overflow: hidden;
      background: #eef3f8;
    }
    .avatar img {
      position: absolute; inset: 0;
      width: 100%; height: 100%;
      display: block;
      transition: opacity .18s ease;
    }
    .avatar img.back { opacity: 0; }
    .avatar.empty img { opacity: .35; filter: grayscale(1); }
    .avatar.empty img.back { opacity: 0; }
    .side { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .age {
      font-size: 13px;
      color: var(--bp-muted);
      min-height: 1.2em;
      font-variant-numeric: tabular-nums;
    }
    .age.preview { color: var(--bp-accent); }
    .fields { display: flex; flex-direction: column; gap: 8px; }
    .selects { display: flex; gap: 8px; flex-wrap: wrap; }
    label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--bp-muted); }
    select, .year-btn {
      font: inherit;
      font-size: 15px;
      line-height: 1.3;
      text-align: left;
      color: var(--bp-text);
      background: var(--bp-bg);
      border: 1px solid var(--bp-border);
      border-radius: var(--bp-radius);
      padding: 7px 28px 7px 10px;
      margin: 0;
      appearance: none; -webkit-appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%236b7280' stroke-width='1.6'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      cursor: pointer;
    }
    select:focus-visible, .year-btn:focus-visible { outline: 2px solid var(--bp-accent); outline-offset: 1px; }
    select.month { min-width: 9.5em; }
    select.day   { min-width: 4.5em; }
    .year-wrap { position: relative; }
    .year-btn { min-width: 5.5em; width: 100%; }
    .year-btn.placeholder { color: var(--bp-text); }
    .year-btn[aria-expanded="true"] { border-color: var(--bp-accent); }
    .year-list {
      position: absolute;
      left: 0; top: calc(100% + 4px);
      z-index: 1000;
      min-width: 100%;
      max-height: 232px;
      overflow-y: auto;
      margin: 0; padding: 4px;
      list-style: none;
      background: var(--bp-bg);
      border: 1px solid var(--bp-border);
      border-radius: var(--bp-radius);
      box-shadow: 0 8px 24px rgba(0,0,0,.12);
      font-size: 15px;
      font-variant-numeric: tabular-nums;
      -webkit-user-select: none; user-select: none;
    }
    .year-list.up { top: auto; bottom: calc(100% + 4px); }
    .year-list[hidden] { display: none; }
    .year-list li {
      padding: 5px 10px;
      border-radius: calc(var(--bp-radius) - 3px);
      cursor: pointer;
      white-space: nowrap;
    }
    .year-list li.hl { background: var(--bp-highlight); color: var(--bp-text); }
    .year-list li[aria-selected="true"] { font-weight: 600; }
    .year-list li[aria-selected="true"]::after { content: " \\2713"; color: var(--bp-accent); }
  `;

  function pad3(n) { return String(n).padStart(3, "0"); }
  function pad2(n) { return String(n).padStart(2, "0"); }
  function daysInMonth(year, month) { return new Date(year, month, 0).getDate(); }

  class BirthdayPicker extends HTMLElement {
    static get formAssociated() { return true; }
    static get observedAttributes() { return ["value", "avatars", "min-year", "max-year", "hide-age"]; }

    constructor() {
      super();
      this._year = null;
      this._month = null;
      this._day = null;
      this._previewYear = null;   // year currently highlighted in the open list (not committed)
      this._frontIsA = true;
      this._typeahead = "";
      this._typeaheadTimer = 0;
      this._internals = typeof this.attachInternals === "function" ? this.attachInternals() : null;

      const root = this.attachShadow({ mode: "open" });
      const uid = "bp" + Math.random().toString(36).slice(2, 8);
      root.innerHTML = `
        <style>${STYLE}</style>
        <div class="side">
          <div class="avatar empty" part="avatar">
            <img class="a" alt="" draggable="false">
            <img class="b back" alt="" draggable="false">
          </div>
          <div class="age" part="age" aria-live="polite"></div>
        </div>
        <div class="fields" part="fields">
          <div class="selects">
            <label>Month<select class="month" part="select month"></select></label>
            <label>Day<select class="day" part="select day"></select></label>
            <label>Year
              <div class="year-wrap">
                <button type="button" class="year-btn placeholder" part="select year" role="combobox"
                        aria-haspopup="listbox" aria-expanded="false" aria-controls="${uid}-list">Year</button>
                <ul class="year-list" part="year-list" id="${uid}-list" role="listbox" tabindex="-1" hidden></ul>
              </div>
            </label>
          </div>
        </div>`;

      this._els = {
        avatar: root.querySelector(".avatar"),
        imgA: root.querySelector("img.a"),
        imgB: root.querySelector("img.b"),
        ageText: root.querySelector(".age"),
        month: root.querySelector("select.month"),
        day: root.querySelector("select.day"),
        yearBtn: root.querySelector(".year-btn"),
        yearList: root.querySelector(".year-list"),
        yearWrap: root.querySelector(".year-wrap"),
      };

      this._els.month.addEventListener("change", () => this._onSelect("month"));
      this._els.day.addEventListener("change", () => this._onSelect("day"));

      // ---- year listbox wiring ----
      const { yearBtn, yearList, yearWrap } = this._els;
      yearBtn.addEventListener("click", () => (this._isOpen() ? this._closeList(false) : this._openList()));
      yearBtn.addEventListener("keydown", (e) => this._onYearKey(e));
      yearList.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus on the button
      yearList.addEventListener("mouseover", (e) => {
        const li = e.target.closest("li[data-year]");
        if (li) this._highlight(+li.dataset.year, false);
      });
      yearList.addEventListener("click", (e) => {
        const li = e.target.closest("li[data-year]");
        if (li) this._commitYear(+li.dataset.year);
      });
      yearWrap.addEventListener("focusout", (e) => {
        if (!yearWrap.contains(e.relatedTarget)) this._closeList(false);
      });
      this._onDocDown = (e) => { if (!e.composedPath().includes(yearWrap)) this._closeList(false); };
    }

    connectedCallback() {
      this._buildMonths();
      this._buildYears();
      this._buildDays();
      if (this.hasAttribute("value")) this._applyValue(this.getAttribute("value"));
      this._render();
    }

    disconnectedCallback() { this._closeList(false); }

    attributeChangedCallback(name, _old, val) {
      if (!this.isConnected) return;
      if (name === "value") this._applyValue(val);
      else if (name === "min-year" || name === "max-year") { this._buildYears(); this._buildDays(); }
      this._render();
    }

    // ----- public API -----
    get year() { return this._year; }
    get month() { return this._month; }
    get day() { return this._day; }
    get age() { return this._computeAge(this._year); }
    get value() {
      return (this._year && this._month && this._day)
        ? `${this._year}-${pad2(this._month)}-${pad2(this._day)}` : "";
    }
    set value(v) { this._applyValue(v); this._render(); }

    // ----- internals -----
    get _minYear() {
      const a = parseInt(this.getAttribute("min-year"), 10);
      return Number.isFinite(a) ? a : new Date().getFullYear() - MAX_AGE;
    }
    get _maxYear() {
      const a = parseInt(this.getAttribute("max-year"), 10);
      return Number.isFinite(a) ? a : new Date().getFullYear();
    }
    get _avatarBase() {
      const base = this.getAttribute("avatars") || DEFAULT_AVATARS;
      return base.endsWith("/") ? base : base + "/";
    }

    _avatarSrc(age) {
      if (INLINE_AVATARS && !this.hasAttribute("avatars")) return INLINE_AVATARS[age];
      return this._avatarBase + "age-" + pad3(age) + ".svg";
    }

    _applyValue(v) {
      const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(v || "");
      if (!m) { this._year = this._month = this._day = null; }
      else {
        this._year = +m[1]; this._month = +m[2]; this._day = +m[3];
        if (this._year < this._minYear || this._year > this._maxYear) this._year = null;
        if (this._month < 1 || this._month > 12) this._month = null;
      }
      this._els.month.value = this._month ?? "";
      this._syncYearButton();
      this._buildDays();
    }

    _option(select, value, label) {
      const o = document.createElement("option");
      o.value = value; o.textContent = label;
      select.appendChild(o);
    }

    _buildMonths() {
      const s = this._els.month;
      s.innerHTML = "";
      this._option(s, "", "Month");
      MONTHS.forEach((name, i) => this._option(s, i + 1, name));
      s.value = this._month ?? "";
    }

    _buildYears() {
      const list = this._els.yearList;
      list.innerHTML = "";
      for (let y = this._maxYear; y >= this._minYear; y--) {
        const li = document.createElement("li");
        li.role = "option";
        li.setAttribute("role", "option");
        li.dataset.year = y;
        li.id = list.id + "-" + y;
        li.textContent = y;
        list.appendChild(li);
      }
      if (this._year !== null && (this._year < this._minYear || this._year > this._maxYear)) this._year = null;
      this._syncYearButton();
    }

    _buildDays() {
      const s = this._els.day;
      const year = this._year ?? 2000;              // leap-safe placeholder when year unknown
      const count = this._month ? daysInMonth(year, this._month) : 31;
      s.innerHTML = "";
      this._option(s, "", "Day");
      for (let d = 1; d <= count; d++) this._option(s, d, d);
      if (this._day !== null && this._day > count) this._day = count;
      s.value = this._day ?? "";
    }

    _syncYearButton() {
      const { yearBtn, yearList } = this._els;
      yearBtn.textContent = this._year ?? "Year";
      yearBtn.classList.toggle("placeholder", this._year === null);
      for (const li of yearList.children) {
        li.setAttribute("aria-selected", +li.dataset.year === this._year ? "true" : "false");
      }
    }

    _onSelect(which) {
      const v = this._els[which].value;
      this["_" + which] = v === "" ? null : +v;
      if (which !== "day") this._buildDays();
      this._render();
      this._emitChange();
    }

    _emitChange() {
      this.dispatchEvent(new CustomEvent("change", {
        bubbles: true, composed: true,
        detail: { year: this._year, month: this._month, day: this._day, age: this.age, value: this.value },
      }));
    }

    // ---- year listbox behaviour ----
    _isOpen() { return !this._els.yearList.hidden; }

    _openList() {
      const { yearBtn, yearList } = this._els;
      if (this._isOpen()) return;
      // open upward if there is not enough room below
      const rect = yearBtn.getBoundingClientRect();
      yearList.classList.toggle("up", window.innerHeight - rect.bottom < 240 && rect.top > 240);
      yearList.hidden = false;
      yearBtn.setAttribute("aria-expanded", "true");
      document.addEventListener("mousedown", this._onDocDown, true);
      this._highlight(this._year ?? this._maxYear, "center");
    }

    _closeList(commit) {
      const { yearBtn, yearList } = this._els;
      if (!this._isOpen()) return;
      if (commit && this._previewYear !== null && this._previewYear !== this._year) {
        this._commitYear(this._previewYear);
        return; // _commitYear closes the list
      }
      yearList.hidden = true;
      yearBtn.setAttribute("aria-expanded", "false");
      yearBtn.removeAttribute("aria-activedescendant");
      document.removeEventListener("mousedown", this._onDocDown, true);
      this._previewYear = null;
      this._render();
    }

    _highlight(year, scroll) {
      const { yearBtn, yearList } = this._els;
      year = Math.max(this._minYear, Math.min(this._maxYear, year));
      this._previewYear = year;
      for (const li of yearList.children) {
        const on = +li.dataset.year === year;
        li.classList.toggle("hl", on);
        if (on) {
          yearBtn.setAttribute("aria-activedescendant", li.id);
          if (scroll) li.scrollIntoView({ block: scroll === "center" ? "center" : "nearest" });
        }
      }
      this._render();
    }

    _commitYear(year) {
      const changed = year !== this._year;
      this._year = year;
      this._previewYear = null;
      this._syncYearButton();
      this._buildDays();
      this._closeList(false);
      this._render();
      if (changed) this._emitChange();
    }

    _onYearKey(e) {
      const open = this._isOpen();
      const cur = open ? (this._previewYear ?? this._year ?? this._maxYear) : (this._year ?? this._maxYear + 1);
      const step = (delta) => {
        e.preventDefault();
        const next = Math.max(this._minYear, Math.min(this._maxYear, cur + delta));
        if (open) this._highlight(next, true);     // preview only
        else this._commitYear(next);               // closed: arrows change the value directly, like a native select
      };
      switch (e.key) {
        case "ArrowDown": step(-1); break;           // list runs newest → oldest, so "down" = earlier year
        case "ArrowUp":   step(+1); break;
        case "PageDown":  step(-10); break;
        case "PageUp":    step(+10); break;
        case "Home":      e.preventDefault(); open ? this._highlight(this._maxYear, true) : this._commitYear(this._maxYear); break;
        case "End":       e.preventDefault(); open ? this._highlight(this._minYear, true) : this._commitYear(this._minYear); break;
        case "Enter":
        case " ":
          e.preventDefault();
          if (open) this._closeList(true); else this._openList();
          break;
        case "Escape":
          if (open) { e.preventDefault(); this._closeList(false); }
          break;
        case "Tab":
          if (open) this._closeList(false);
          break;
        default:
          if (/^\d$/.test(e.key)) {                 // type-ahead: "19", "198", "1984"
            e.preventDefault();
            clearTimeout(this._typeaheadTimer);
            this._typeahead += e.key;
            this._typeaheadTimer = setTimeout(() => { this._typeahead = ""; }, 900);
            if (!open) this._openList();
            const match = [...this._els.yearList.children].find((li) => li.dataset.year.startsWith(this._typeahead));
            if (match) this._highlight(+match.dataset.year, true);
          }
      }
    }

    _computeAge(year) {
      if (year === null || year === undefined) return null;
      const now = new Date();
      let age = now.getFullYear() - year;
      if (this._month !== null) {
        const bm = this._month - 1, bd = this._day ?? 1;
        if (now.getMonth() < bm || (now.getMonth() === bm && now.getDate() < bd)) age -= 1;
      }
      return Math.max(0, Math.min(MAX_AGE, age));
    }

    _render() {
      const previewing = this._previewYear !== null;
      const age = this._computeAge(previewing ? this._previewYear : this._year);
      const { avatar, imgA, imgB, ageText } = this._els;
      const src = this._avatarSrc(age ?? 30);

      avatar.classList.toggle("empty", age === null);
      const front = this._frontIsA ? imgA : imgB;
      const back = this._frontIsA ? imgB : imgA;
      if (front.getAttribute("src") !== src) {
        if (!front.getAttribute("src")) {
          front.src = src;                          // first paint: no crossfade needed
        } else {
          back.src = src;
          back.classList.remove("back");
          front.classList.add("back");
          this._frontIsA = !this._frontIsA;
        }
      }
      ageText.textContent = (this.hasAttribute("hide-age") || age === null) ? "" : `Age ${age}`;
      ageText.classList.toggle("preview", previewing);
      avatar.setAttribute("aria-label", age === null ? "No birthday selected" : `Avatar for age ${age}`);

      if (this._internals) this._internals.setFormValue(this.value || null);
    }
  }

  if (!customElements.get("birthday-picker")) customElements.define("birthday-picker", BirthdayPicker);
})();
