/* ---------------------------------------------------------------------
   Pharmacy Intelligence -- app shell + router + page renderers
--------------------------------------------------------------------- */

const NAV_ITEMS = [
  { id: "dashboard", label: "الرئيسية" },
  { id: "executive", label: "الملخص التنفيذي" },
  { id: "sales", label: "المبيعات" },
  { id: "inventory", label: "المخزون" },
  { id: "purchases", label: "المشتريات" },
  { id: "profit", label: "الربحية" },
  { id: "expiry", label: "الصلاحية" },
  { id: "dead-stock", label: "الأصناف الراكدة" },
  { id: "associations", label: "أنماط الشراء" },
  { id: "forecast", label: "التوقعات" },
  { id: "data-quality", label: "جودة البيانات" },
  { id: "import", label: "استيراد البيانات" },
];

const fmtMoney = (v) => `${Number(v || 0).toLocaleString("en-US", { maximumFractionDigits: 0 })} د.ل`;
const fmtNum = (v) => Number(v || 0).toLocaleString("en-US");
const fmtPct = (v) => (v === null || v === undefined ? "—" : `${v > 0 ? "+" : ""}${v}%`);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ------------------------------------------------------------- landing */
function initLanding() {
  document.getElementById("btn-start-demo").addEventListener("click", () => showDemoDataScreen());
  document.getElementById("btn-upload-data").addEventListener("click", () => {
    document.getElementById("landing").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
    initShell();
    navigate("import");
  });
  document.getElementById("btn-explore-integration").addEventListener("click", () => {
    alert("يمكن إعداد طريقة مزامنة مناسبة بعد دراسة منظومة الصيدلية المستخدمة. للتجربة الآن، استخدم البيانات التجريبية أو ارفع ملف CSV/Excel.");
  });
}

async function showDemoDataScreen() {
  document.getElementById("landing").classList.add("hidden");
  const screen = document.getElementById("demo-preview-screen");
  screen.classList.remove("hidden");
  screen.innerHTML = `<div class="container" style="padding-top:32px;padding-bottom:60px;">
    <div class="state-box"><div class="spinner" style="margin:0 auto"></div><p style="margin-top:12px">جاري تحميل بيانات الصيدلية التجريبية...</p></div>
  </div>`;

  try {
    const summary = await apiGet("/demo/summary");
    renderDemoPreview(summary);
  } catch (e) {
    screen.innerHTML = `<div class="container" style="padding-top:32px"><div class="state-box"><h3>تعذّر تحميل البيانات</h3><p>${esc(e.message)}. تأكد من تشغيل الخادم (python backend/app.py).</p></div></div>`;
  }
}

function renderDemoPreview(summary) {
  const screen = document.getElementById("demo-preview-screen");
  screen.innerHTML = `
    <div class="container" style="padding-top:28px;padding-bottom:70px;">
      <span class="demo-banner">بيانات اصطناعية &middot; DEMO DATA</span>
      <h1 style="margin-bottom:6px;">بيانات الصيدلية التجريبية</h1>
      <p class="muted" style="margin-bottom:22px;">البيانات المعروضة أدناه اصطناعية ومولدة لأغراض العرض. لا تمثل صيدلية حقيقية ولا تحتوي على بيانات عملاء حقيقيين.</p>

      <div class="kpi-grid" style="margin-bottom:28px;">
        ${kpiCard("الفترة", `${summary.period_start} — ${summary.period_end}`)}
        ${kpiCard("عدد المنتجات", fmtNum(summary.product_count))}
        ${kpiCard("فواتير البيع", fmtNum(summary.sales_invoice_count))}
        ${kpiCard("فواتير الشراء", fmtNum(summary.purchase_invoice_count))}
        ${kpiCard("الوحدات المباعة", fmtNum(summary.total_units_sold))}
        ${kpiCard("عدد الموردين", fmtNum(summary.supplier_count))}
        ${kpiCard("قيمة المخزون", fmtMoney(summary.stock_value))}
      </div>

      <div class="card" style="margin-bottom:24px;">
        <div class="tabs" id="preview-tabs">
          ${["sales", "purchases", "inventory", "products"].map((t, i) =>
            `<button class="tab-btn ${i === 0 ? "active" : ""}" data-tab="${t}">${previewTabLabel(t)}</button>`).join("")}
        </div>
        <div id="preview-table-toolbar" class="table-toolbar">
          <input type="text" id="preview-search" placeholder="بحث..." />
        </div>
        <div id="preview-table-root"></div>
      </div>

      <div class="card" style="text-align:center;">
        <h2 style="margin-bottom:8px;">تحليل بيانات الصيدلية</h2>
        <p class="muted" style="margin-bottom:18px;">سنحلل المبيعات والمخزون والمشتريات والصلاحية والربحية وأنماط الطلب.</p>
        <button class="btn btn-primary btn-lg" id="btn-run-analysis">ابدأ التحليل</button>
      </div>
    </div>`;

  let currentTab = "sales";
  let currentPage = 1;
  let searchTerm = "";

  const loadTable = async () => {
    const root = document.getElementById("preview-table-root");
    root.innerHTML = `<div class="state-box"><div class="spinner" style="margin:0 auto"></div></div>`;
    const q = new URLSearchParams({ page: currentPage, page_size: 20, search: searchTerm });
    const data = await apiGet(`/demo/table/${currentTab}?${q}`);
    root.innerHTML = renderPreviewTable(currentTab, data);
    document.querySelectorAll("#preview-table-root .page-btn").forEach((btn) => {
      btn.addEventListener("click", () => { currentPage = Number(btn.dataset.page); loadTable(); });
    });
  };

  document.querySelectorAll("#preview-tabs .tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#preview-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentTab = btn.dataset.tab; currentPage = 1; searchTerm = "";
      document.getElementById("preview-search").value = "";
      loadTable();
    });
  });
  document.getElementById("preview-search").addEventListener("input", debounce((e) => {
    searchTerm = e.target.value; currentPage = 1; loadTable();
  }, 300));

  document.getElementById("btn-run-analysis").addEventListener("click", runAnalysisSequence);

  loadTable();
}

function previewTabLabel(t) {
  return { sales: "المبيعات", purchases: "المشتريات", inventory: "المخزون", products: "المنتجات" }[t];
}

const TABLE_COLUMNS = {
  sales: [["invoice_no", "رقم الفاتورة"], ["date", "التاريخ"], ["time", "الوقت"], ["barcode", "الباركود"],
    ["product_name", "اسم الصنف"], ["category", "الفئة"], ["quantity", "الكمية"], ["selling_price", "سعر البيع"],
    ["purchase_price", "سعر الشراء"], ["revenue", "الإيراد"], ["profit", "الربح"]],
  purchases: [["po_no", "رقم فاتورة الشراء"], ["date", "التاريخ"], ["supplier", "المورد"], ["barcode", "الباركود"],
    ["product_name", "الصنف"], ["quantity", "الكمية"], ["purchase_price", "سعر الشراء"], ["total", "الإجمالي"]],
  inventory: [["barcode", "الباركود"], ["product_name", "الصنف"], ["category", "الفئة"],
    ["quantity_on_hand", "الكمية الحالية"], ["purchase_price", "سعر الشراء"], ["selling_price", "سعر البيع"],
    ["stock_value", "قيمة المخزون"], ["expiry_date", "تاريخ الصلاحية"], ["supplier", "المورد"]],
  products: [["barcode", "الباركود"], ["product_name", "اسم الصنف"], ["category", "الفئة"],
    ["manufacturer", "الشركة المصنعة"], ["unit", "الوحدة"], ["purchase_price", "سعر الشراء"], ["selling_price", "سعر البيع"]],
};

function renderPreviewTable(tab, data) {
  const cols = TABLE_COLUMNS[tab];
  if (!data.rows.length) return emptyState("لا توجد نتائج", "جرّب مصطلح بحث مختلف.");
  const head = cols.map(([, label]) => `<th>${label}</th>`).join("");
  const body = data.rows.map((r) => `<tr>${cols.map(([key]) => `<td class="${typeof r[key] === "number" ? "numeric" : ""}">${esc(r[key])}</td>`).join("")}</tr>`).join("");
  return `<div class="table-wrap"><table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>
    ${pagination(data)}`;
}

function pagination(data) {
  const { page, total_pages } = data;
  return `<div class="pagination">
    <button class="btn page-btn" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>التالي ‹</button>
    <span class="tiny muted">صفحة ${page} من ${total_pages} &middot; ${fmtNum(data.total_rows)} صف</span>
    <button class="btn page-btn" data-page="${page + 1}" ${page >= total_pages ? "disabled" : ""}>› السابق</button>
  </div>`;
}

function kpiCard(label, value, changePct) {
  let change = "";
  if (changePct !== undefined && changePct !== null) {
    change = `<div class="kpi-change ${changePct >= 0 ? "up" : "down"}">${fmtPct(changePct)} مقارنة بالفترة السابقة</div>`;
  }
  return `<div class="kpi-card"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div>${change}</div>`;
}

function emptyState(title, body) {
  return `<div class="state-box"><h3>${esc(title)}</h3><p>${esc(body)}</p></div>`;
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

/* ------------------------------------------------------- processing UI */
async function runAnalysisSequence() {
  const screen = document.getElementById("demo-preview-screen");
  const steps = [
    "جاري التحقق من البيانات...", "جاري تحليل المبيعات...", "جاري تحليل المخزون...",
    "جاري حساب معدلات البيع...", "جاري اكتشاف الأصناف الراكدة...", "جاري تحليل الصلاحيات...",
    "جاري اكتشاف أنماط الشراء...", "جاري إنشاء التوقعات...",
  ];
  screen.innerHTML = `<div class="container" style="padding-top:60px;"><div class="process-steps" id="process-steps"></div></div>`;
  const list = document.getElementById("process-steps");

  try {
    for (let i = 0; i < steps.length; i++) {
      const row = document.createElement("div");
      row.className = "process-step active";
      row.innerHTML = `<span class="status"><span class="spinner"></span></span><span>${steps[i]}</span>`;
      list.appendChild(row);
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, 260));
      row.classList.remove("active"); row.classList.add("done");
      row.querySelector(".status").textContent = "✓";
    }
    await apiPost("/analyze", {});
    await new Promise((r) => setTimeout(r, 200));
  } catch (e) {
    list.innerHTML = emptyState("تعذّر إكمال التحليل", e.message);
    return;
  }

  document.getElementById("demo-preview-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  initShell();
  navigate("dashboard");
}

/* ------------------------------------------------------------- shell */
let shellInitialized = false;
function initShell() {
  if (shellInitialized) return;
  shellInitialized = true;

  const sidebar = document.getElementById("sidebar");
  sidebar.innerHTML = `
    <div class="sidebar-brand"><span class="dot"></span> منصة ذكاء الصيدليات</div>
    <div class="nav-group" id="nav-group"></div>
    <div style="margin-top:auto;padding:14px 16px;">
      <span class="badge badge-demo">نسخة تجريبية &middot; بيانات اصطناعية</span>
    </div>`;
  const navGroup = document.getElementById("nav-group");
  navGroup.innerHTML = NAV_ITEMS.map((n) =>
    `<div class="nav-item" data-nav="${n.id}"><span class="icon"></span>${n.label}</div>`).join("");
  navGroup.querySelectorAll(".nav-item").forEach((el) => {
    el.addEventListener("click", () => { navigate(el.dataset.nav); closeSidebar(); });
  });

  const bottomNav = document.getElementById("bottom-nav");
  const bottomItems = NAV_ITEMS.slice(0, 8);
  bottomNav.innerHTML = `<div class="bottom-nav-inner">${bottomItems.map((n) =>
    `<div class="bottom-nav-item" data-nav="${n.id}"><span class="icon"></span>${n.label}</div>`).join("")}</div>`;
  bottomNav.querySelectorAll(".bottom-nav-item").forEach((el) => {
    el.addEventListener("click", () => navigate(el.dataset.nav));
  });

  document.getElementById("menu-toggle").addEventListener("click", () => {
    sidebar.classList.add("open");
    document.getElementById("sidebar-scrim").classList.add("open");
  });
  document.getElementById("sidebar-scrim").addEventListener("click", closeSidebar);
  document.getElementById("btn-back-to-demo").addEventListener("click", () => {
    document.getElementById("app-shell").classList.add("hidden");
    showDemoDataScreen();
  });
}

function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebar-scrim").classList.remove("open");
}

function setActiveNav(id) {
  document.querySelectorAll(".nav-item, .bottom-nav-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === id);
  });
  const item = NAV_ITEMS.find((n) => n.id === id);
  document.getElementById("topbar-title").textContent = item ? item.label : "";
}

/* -------------------------------------------------------------- router */
const routes = {
  dashboard: renderDashboard,
  executive: renderExecutive,
  sales: renderSales,
  inventory: renderInventory,
  purchases: renderPurchasesTable,
  profit: renderProfit,
  expiry: renderExpiry,
  "dead-stock": renderDeadStock,
  associations: renderAssociations,
  forecast: renderForecast,
  "data-quality": renderDataQuality,
  import: renderImportWizard,
};

async function navigate(id) {
  setActiveNav(id);
  const root = document.getElementById("view-root");
  root.innerHTML = `<div class="state-box"><div class="spinner" style="margin:0 auto"></div><p style="margin-top:10px">جاري التحميل...</p></div>`;
  window.scrollTo(0, 0);
  try {
    const renderer = routes[id] || renderDashboard;
    await renderer(root);
  } catch (e) {
    root.innerHTML = emptyState("حدث خطأ", e.message);
  }
}

/* -------------------------------------------------------------- pages */
async function renderDashboard(root) {
  const data = await apiGet("/dashboard");
  const c = data.period.current, ch = data.period.change_pct;
  const attn = [];
  if (data.attention.low_stock_count) attn.push({ level: "danger", text: `${data.attention.low_stock_count} أصناف قد تنفد خلال 7 أيام`, nav: "inventory" });
  if (data.attention.expiry_7_days_count) attn.push({ level: "warning", text: `${data.attention.expiry_7_days_count} أصناف قريبة من انتهاء الصلاحية`, nav: "expiry" });
  if (data.attention.dead_stock_count) attn.push({ level: "warning", text: `${data.attention.dead_stock_count} صنفًا راكدًا بقيمة ${fmtMoney(data.attention.dead_stock_value)}`, nav: "dead-stock" });
  attn.push({ level: ch.revenue >= 0 ? "success" : "danger", text: `المبيعات ${ch.revenue >= 0 ? "ارتفعت" : "انخفضت"} ${Math.abs(ch.revenue)}% مقارنة بالشهر السابق`, nav: "sales" });

  root.innerHTML = `
    <h1 style="margin-bottom:4px;">ماذا يحتاج مدير الصيدلية إلى معرفته اليوم؟</h1>
    <p class="muted" style="margin-bottom:22px;">آخر 30 يومًا من بيانات الصيدلية التجريبية</p>

    <div class="section-title"><h2>ملخص الفترة</h2></div>
    <div class="kpi-grid" style="margin-bottom:28px;">
      ${kpiCard("إجمالي المبيعات", fmtMoney(c.revenue), ch.revenue)}
      ${kpiCard("إجمالي الربح", fmtMoney(c.profit), ch.profit)}
      ${kpiCard("عدد الفواتير", fmtNum(c.invoices), ch.invoices)}
      ${kpiCard("الوحدات المباعة", fmtNum(c.units_sold), ch.units_sold)}
      ${kpiCard("أصناف منخفضة المخزون", fmtNum(data.attention.low_stock_count))}
      ${kpiCard("أصناف راكدة", fmtNum(data.attention.dead_stock_count))}
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="section-title"><h2>يحتاج انتباهك</h2></div>
        <div class="attn-list">
          ${attn.map((a) => `<div class="attn-item level-${a.level}" data-nav="${a.nav}"><span class="attn-dot"></span><span class="attn-text">${a.text}</span></div>`).join("")}
        </div>
      </div>
      <div class="card">
        <div class="section-title"><h2>أفضل المنتجات إيرادًا</h2></div>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>المنتج</th><th>الإيراد</th><th>الربح</th></tr></thead>
          <tbody>${data.top_products.map((p) => `<tr><td>${esc(p.product_name)}</td><td class="numeric">${fmtMoney(p.revenue)}</td><td class="numeric">${fmtMoney(p.profit)}</td></tr>`).join("")}</tbody>
        </table></div>
      </div>
    </div>`;

  root.querySelectorAll(".attn-item").forEach((el) => el.addEventListener("click", () => navigate(el.dataset.nav)));
}

async function renderExecutive(root) {
  const data = await apiGet("/executive-summary");
  const section = (title, items, emptyText) => `
    <div class="card">
      <h3 style="margin-bottom:10px;">${title}</h3>
      ${items.length ? `<ul style="margin:0;padding-inline-start:18px;display:flex;flex-direction:column;gap:8px;">${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : `<p class="muted">${emptyText}</p>`}
    </div>`;
  root.innerHTML = `
    <h1 style="margin-bottom:18px;">الملخص التنفيذي</h1>
    <div class="stack">
      ${section("أهم ما حدث", data.highlights, "لا توجد مستجدات بارزة.")}
      ${section("أهم المخاطر", data.risks, "لا توجد مخاطر بارزة حاليًا.")}
      ${section("أهم الفرص", data.opportunities, "لا توجد فرص بارزة حاليًا.")}
      ${section("الإجراءات المقترحة", data.actions, "لا توجد إجراءات مقترحة حاليًا.")}
    </div>`;
}

async function renderSales(root) {
  root.innerHTML = `
    <div class="section-title"><h1>المبيعات</h1>
      <select id="sales-range" class="btn"><option value="30d">آخر 30 يومًا</option><option value="90d">آخر 90 يومًا</option><option value="6m">آخر 6 أشهر</option></select>
    </div>
    <div id="sales-body"><div class="state-box"><div class="spinner" style="margin:0 auto"></div></div></div>`;

  const load = async () => {
    const range = document.getElementById("sales-range").value;
    const data = await apiGet(`/sales?range=${range}`);
    const c = data.comparison.current, ch = data.comparison.change_pct;
    document.getElementById("sales-body").innerHTML = `
      <div class="kpi-grid" style="margin:18px 0;">
        ${kpiCard("إجمالي المبيعات", fmtMoney(c.revenue), ch.revenue)}
        ${kpiCard("عدد الفواتير", fmtNum(c.invoices), ch.invoices)}
        ${kpiCard("متوسط قيمة الفاتورة", fmtMoney(c.avg_invoice_value))}
        ${kpiCard("الوحدات المباعة", fmtNum(c.units_sold), ch.units_sold)}
      </div>
      <div class="chart-card" style="margin-bottom:18px;">
        <h3 style="margin-bottom:10px;">المبيعات عبر الزمن</h3>
        <div class="chart-wrap"><canvas id="chart-sales-trend"></canvas></div>
      </div>
      <div class="grid-2" style="margin-bottom:18px;">
        <div class="chart-card"><h3 style="margin-bottom:10px;">المبيعات حسب اليوم</h3><div class="chart-wrap"><canvas id="chart-weekday"></canvas></div></div>
        <div class="chart-card"><h3 style="margin-bottom:10px;">ساعات الذروة</h3><div class="chart-wrap"><canvas id="chart-hours"></canvas></div></div>
      </div>
      <div class="grid-2">
        <div class="card"><h3 style="margin-bottom:10px;">أفضل المنتجات</h3>${simpleList(data.top_products, "product_name", "revenue")}</div>
        <div class="card"><h3 style="margin-bottom:10px;">أفضل الفئات</h3>${simpleList(data.top_categories, "category", "revenue")}</div>
      </div>`;

    renderLineChart("chart-sales-trend", data.trend.map((t) => t.date), [{ label: "الإيراد", data: data.trend.map((t) => t.revenue) }]);
    renderBarChart("chart-weekday", data.weekday.map((w) => arabicWeekday(w.weekday)), data.weekday.map((w) => w.revenue));
    renderBarChart("chart-hours", data.peak_hours.all_hours.map((h) => `${h.hour}:00`), data.peak_hours.all_hours.map((h) => h.revenue), { color: CHART_COLORS.secondary });
  };
  document.getElementById("sales-range").addEventListener("change", load);
  await load();
}

function arabicWeekday(code) {
  return { Mon: "الإثنين", Tue: "الثلاثاء", Wed: "الأربعاء", Thu: "الخميس", Fri: "الجمعة", Sat: "السبت", Sun: "الأحد" }[code];
}

function simpleList(rows, nameKey, valueKey) {
  if (!rows.length) return emptyState("لا توجد بيانات", "");
  return `<div style="display:flex;flex-direction:column;gap:8px;">${rows.slice(0, 8).map((r) =>
    `<div style="display:flex;justify-content:space-between;font-size:13.5px;"><span>${esc(r[nameKey])}</span><span class="numeric muted">${fmtMoney(r[valueKey])}</span></div>`).join("")}</div>`;
}

async function renderInventory(root) {
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">المخزون</h1>
    <p class="muted" style="margin-bottom:18px;">الأصناف منخفضة المخزون واقتراحات إعادة الطلب، بناءً على متوسط البيع اليومي لآخر 30 يومًا.</p>
    <div class="tabs">
      <button class="tab-btn active" data-tab="low-stock">منخفضة المخزون</button>
      <button class="tab-btn" data-tab="reorder">اقتراحات إعادة الطلب</button>
    </div>
    <div id="inv-body"></div>`;

  const [lowStock, reorder] = await Promise.all([apiGet("/inventory/low-stock"), apiGet("/inventory/reorder")]);

  const show = (tab) => {
    const body = document.getElementById("inv-body");
    if (tab === "low-stock") {
      if (!lowStock.length) { body.innerHTML = emptyState("لا توجد أصناف منخفضة المخزون حاليًا", "كل الأصناف ضمن المستوى الآمن."); return; }
      body.innerHTML = `<div class="table-wrap"><table class="data-table">
        <thead><tr><th>الصنف</th><th>الفئة</th><th>المخزون الحالي</th><th>متوسط البيع اليومي</th><th>التقدير</th></tr></thead>
        <tbody>${lowStock.map((r) => `<tr><td>${esc(r.product_name)}</td><td>${esc(r.category)}</td><td class="numeric">${r.quantity_on_hand}</td><td class="numeric">${r.avg_daily_sales}</td>
          <td>${r.days_of_stock_left <= 0 ? "نافد الآن" : `تقديريًا، قد ينفد خلال ${Math.round(r.days_of_stock_left)} يوم`}</td></tr>`).join("")}</tbody>
      </table></div>`;
    } else {
      if (!reorder.length) { body.innerHTML = emptyState("لا توجد اقتراحات حاليًا", ""); return; }
      body.innerHTML = `<div class="table-wrap"><table class="data-table">
        <thead><tr><th>الصنف</th><th>المخزون الحالي</th><th>متوسط البيع اليومي</th><th>الكمية المقترحة للطلب</th></tr></thead>
        <tbody>${reorder.map((r) => `<tr><td>${esc(r.product_name)}</td><td class="numeric">${r.quantity_on_hand}</td><td class="numeric">${r.avg_daily_sales}</td><td class="numeric">${fmtNum(r.suggested_qty)}</td></tr>`).join("")}</tbody>
      </table></div>`;
    }
  };
  root.querySelectorAll(".tab-btn").forEach((btn) => btn.addEventListener("click", () => {
    root.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active")); btn.classList.add("active"); show(btn.dataset.tab);
  }));
  show("low-stock");
}

async function renderPurchasesTable(root) {
  root.innerHTML = `<h1 style="margin-bottom:14px;">المشتريات</h1>
    <div class="table-toolbar"><input type="text" id="purch-search" placeholder="بحث عن مورد أو صنف..." /></div>
    <div id="purch-table-root"></div>`;
  let page = 1, search = "";
  const load = async () => {
    const q = new URLSearchParams({ page, page_size: 20, search });
    const data = await apiGet(`/demo/table/purchases?${q}`);
    document.getElementById("purch-table-root").innerHTML = renderPreviewTable("purchases", data);
    document.querySelectorAll("#purch-table-root .page-btn").forEach((b) => b.addEventListener("click", () => { page = Number(b.dataset.page); load(); }));
  };
  document.getElementById("purch-search").addEventListener("input", debounce((e) => { search = e.target.value; page = 1; load(); }, 300));
  await load();
}

async function renderProfit(root) {
  const data = await apiGet("/profit");
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">الربحية</h1>
    <p class="muted" style="margin-bottom:18px;">الإيراد هو إجمالي المبيعات، والربح هو الإيراد بعد خصم التكلفة، وهامش الربح هو نسبة الربح إلى الإيراد. منتج قد يكون الأكثر مبيعًا لكنه ليس الأكثر ربحًا.</p>
    <div class="grid-2" style="margin-bottom:18px;">
      <div class="card"><h3 style="margin-bottom:10px;">أكثر المنتجات ربحًا</h3>${profitTable(data.top_profit, "profit")}</div>
      <div class="card"><h3 style="margin-bottom:10px;">أكثر المنتجات إيرادًا</h3>${profitTable(data.top_revenue, "revenue")}</div>
    </div>
    <div class="grid-2">
      <div class="card"><h3 style="margin-bottom:10px;">أعلى هامش ربح</h3>${profitTable(data.top_margin, "margin_pct", "%")}</div>
      <div class="card"><h3 style="margin-bottom:10px;">مبيعات عالية بهامش منخفض</h3>${profitTable(data.high_volume_low_margin, "margin_pct", "%")}</div>
    </div>`;
}

function profitTable(rows, valueKey, suffix) {
  if (!rows.length) return emptyState("لا توجد بيانات", "");
  return `<div class="table-wrap"><table class="data-table"><thead><tr><th>المنتج</th><th>القيمة</th></tr></thead>
    <tbody>${rows.slice(0, 10).map((r) => `<tr><td>${esc(r.product_name)}</td><td class="numeric">${suffix ? r[valueKey] + suffix : fmtMoney(r[valueKey])}</td></tr>`).join("")}</tbody>
  </table></div>`;
}

async function renderExpiry(root) {
  const data = await apiGet("/expiry");
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">الصلاحية</h1>
    <p class="muted" style="margin-bottom:18px;">هذه تقديرات إحصائية مبنية على متوسط البيع اليومي، وليست توصية طبية. قيمة المخزون المعرض للخطر: <strong>${fmtMoney(data.value_at_risk)}</strong></p>
    <div class="tabs">
      ${[["7_days", "خلال 7 أيام"], ["30_days", "خلال 30 يومًا"], ["90_days", "خلال 90 يومًا"]].map(([k, l], i) =>
        `<button class="tab-btn ${i === 0 ? "active" : ""}" data-tab="${k}">${l} (${data.counts[k]})</button>`).join("")}
    </div>
    <div id="expiry-body"></div>`;

  const show = (bucket) => {
    const rows = data.buckets[bucket];
    const body = document.getElementById("expiry-body");
    if (!rows.length) { body.innerHTML = emptyState("لا توجد أصناف في هذه الفئة", ""); return; }
    body.innerHTML = `<div class="table-wrap"><table class="data-table">
      <thead><tr><th>المنتج</th><th>الكمية</th><th>تاريخ الانتهاء</th><th>المبيعات المتوقعة قبل الانتهاء</th><th>الوحدات المعرضة للخطر</th><th>قيمة المخزون</th></tr></thead>
      <tbody>${rows.map((r) => `<tr><td>${esc(r.product_name)}</td><td class="numeric">${r.quantity_on_hand}</td><td>${r.expiry_date}</td>
        <td class="numeric">${r.estimated_units_sold_before_expiry}</td><td class="numeric">${r.estimated_units_at_risk}</td><td class="numeric">${fmtMoney(r.stock_value)}</td></tr>`).join("")}</tbody>
    </table></div>`;
  };
  root.querySelectorAll(".tab-btn").forEach((btn) => btn.addEventListener("click", () => {
    root.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active")); btn.classList.add("active"); show(btn.dataset.tab);
  }));
  show("7_days");
}

async function renderDeadStock(root) {
  const data = await apiGet("/inventory/dead-stock");
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">الأصناف الراكدة</h1>
    <p class="muted" style="margin-bottom:18px;">${data.total_count} صنفًا لم يتحرك مؤخرًا، بقيمة مخزون إجمالية ${fmtMoney(data.total_value)}.</p>
    ${data.rows.length ? `<div class="table-wrap"><table class="data-table">
      <thead><tr><th>المنتج</th><th>الفئة</th><th>الكمية</th><th>قيمة المخزون</th><th>عدد أيام عدم الحركة</th></tr></thead>
      <tbody>${data.rows.map((r) => `<tr><td>${esc(r.product_name)}</td><td>${esc(r.category)}</td><td class="numeric">${r.quantity_on_hand}</td>
        <td class="numeric">${fmtMoney(r.stock_value)}</td><td>${r.days_since_last_sale >= 999 ? "لم يُبع خلال الفترة" : `${r.days_since_last_sale} يومًا`}</td></tr>`).join("")}</tbody>
    </table></div>` : emptyState("لا توجد أصناف راكدة", "")}`;
}

async function renderAssociations(root) {
  const rows = await apiGet("/associations");
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">أنماط الشراء</h1>
    <p class="muted" style="margin-bottom:18px;">يظهر ارتباط شرائي متكرر بين هذه المنتجات، بناءً على بيانات الفواتير. هذه ملاحظات تحليلية للترويج المتقاطع، وليست توصيات علاجية.</p>
    ${rows.length ? `<div style="display:flex;flex-direction:column;gap:10px;">${rows.map((r) => `
      <div class="assoc-card">
        <div class="assoc-names">${esc(r.product_a)} + ${esc(r.product_b)}</div>
        <div class="assoc-stats">
          <span>التكرار: ${r.frequency}</span>
          <span>Confidence: ${(r.confidence * 100).toFixed(0)}%</span>
          <span>Support: ${(r.support * 100).toFixed(1)}%</span>
        </div>
      </div>`).join("")}</div>` : emptyState("لا توجد أنماط واضحة", "")}`;
}

async function renderForecast(root) {
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">توقع الطلب</h1>
    <p class="muted" style="margin-bottom:18px;">توقع مبني على اتجاه المبيعات خلال آخر 60 يومًا. الأرقام تقديرية وليست حقائق مؤكدة.</p>
    <div class="chart-card"><div class="chart-wrap"><canvas id="chart-forecast"></canvas></div></div>`;
  const data = await apiGet("/forecast?days=14");
  if (!data.history.length) { root.querySelector(".chart-card").innerHTML = emptyState("بيانات غير كافية للتوقع", ""); return; }
  renderForecastChart("chart-forecast", data.history, data.forecast);
}

async function renderDataQuality(root) {
  const data = await apiGet("/data-quality");
  const color = data.quality_score >= 90 ? "success" : data.quality_score >= 70 ? "warning" : "danger";
  root.innerHTML = `
    <h1 style="margin-bottom:18px;">جودة البيانات</h1>
    <div class="card" style="margin-bottom:18px;">
      <div class="quality-gauge">
        <div class="quality-number" style="color:var(--color-${color})">${data.quality_score}%</div>
        <div><p style="font-weight:600;">Data Quality Score</p><p class="muted tiny">مبني على ${fmtNum(data.row_count)} صف من بيانات المبيعات</p></div>
      </div>
    </div>
    <div class="kpi-grid" style="margin-bottom:18px;">
      ${kpiCard("أسعار مفقودة", fmtNum(data.missing_prices))}
      ${kpiCard("صفوف مكررة", fmtNum(data.duplicates))}
      ${kpiCard("تواريخ غير صالحة", fmtNum(data.invalid_dates))}
      ${kpiCard("منتجات غير معروفة", fmtNum(data.missing_products))}
    </div>
    ${data.issues.length ? `<div class="card"><h3 style="margin-bottom:10px;">الملاحظات</h3><ul style="margin:0;padding-inline-start:18px;display:flex;flex-direction:column;gap:6px;">
      ${data.issues.map((i) => `<li class="${i.level === "error" ? "" : ""}">${esc(i.message)}</li>`).join("")}</ul></div>` : emptyState("لا توجد ملاحظات", "البيانات نظيفة.")}`;
}
