/* Renders the "استيراد البيانات" page: a 4-step wizard for CSV/Excel upload. */

const IMPORT_STANDARD_FIELDS = {
  sales: [["product_name", "اسم الصنف"], ["quantity", "الكمية"], ["date", "تاريخ البيع"],
    ["selling_price", "سعر البيع"], ["purchase_price", "سعر الشراء"], ["barcode", "الباركود"],
    ["invoice_no", "رقم الفاتورة"], ["category", "الفئة"]],
  purchases: [["product_name", "الصنف"], ["quantity", "الكمية"], ["date", "التاريخ"],
    ["purchase_price", "سعر الشراء"], ["supplier", "المورد"], ["barcode", "الباركود"], ["po_no", "رقم فاتورة الشراء"]],
  inventory: [["product_name", "الصنف"], ["quantity_on_hand", "الكمية الحالية"], ["purchase_price", "سعر الشراء"],
    ["selling_price", "سعر البيع"], ["expiry_date", "تاريخ الصلاحية"], ["barcode", "الباركود"], ["category", "الفئة"]],
};

async function renderImportWizard(root) {
  root.innerHTML = `
    <h1 style="margin-bottom:6px;">أريد تحليل بيانات صيدليتي</h1>
    <p class="muted" style="margin-bottom:18px;">ارفع ملف CSV أو Excel من منظومة الصيدلية، وسنقوم بتهيئته وتحليله. لا تحتاج إلى تغيير منظومة الصيدلية الحالية.</p>

    <div class="wizard-steps">
      <span class="wizard-step-pill active" data-step="1">1. رفع الملف</span>
      <span class="wizard-step-pill" data-step="2">2. تحديد الأعمدة</span>
      <span class="wizard-step-pill" data-step="3">3. التحقق</span>
      <span class="wizard-step-pill" data-step="4">4. التحليل</span>
    </div>

    <div class="card">
      <div style="margin-bottom:14px;">
        <label class="tiny muted" style="display:block;margin-bottom:6px;">نوع البيانات</label>
        <select id="import-table-type" class="btn">
          <option value="sales">مبيعات</option>
          <option value="purchases">مشتريات</option>
          <option value="inventory">مخزون</option>
        </select>
      </div>
      <div class="dropzone" id="dropzone">
        <p style="font-weight:600;margin-bottom:6px;">اسحب الملف هنا أو اضغط للاختيار</p>
        <p class="tiny">يدعم ملفات CSV و Excel (.xlsx, .xls)</p>
        <input type="file" id="file-input" accept=".csv,.xlsx,.xls" style="display:none;" />
      </div>
      <div id="wizard-body" style="margin-top:18px;"></div>
    </div>

    <div class="grid-3" style="margin-top:24px;">
      ${importMethodCard("ملفات متعددة", "يمكن رفع Sales.csv و Purchases.csv و Inventory.csv و Products.csv بشكل منفصل، كل ملف على حدة.")}
      ${importMethodCard("API", "إذا كانت منظومة الصيدلية توفر API، يمكن إعداد اتصال مباشر لاحقًا.")}
      ${importMethodCard("Local Connector", "برنامج صغير يعمل على جهاز الصيدلية ويرسل البيانات بشكل آمن -- قيد الإعداد.")}
    </div>`;

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  dropzone.addEventListener("click", () => fileInput.click());
  ["dragover", "dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.toggle("dragover", evt === "dragover");
    });
  });
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });
  fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  });
}

function importMethodCard(title, body) {
  return `<div class="card"><h3 style="margin-bottom:8px;">${title}</h3><p class="muted tiny">${body}</p></div>`;
}

function setWizardStep(n) {
  document.querySelectorAll(".wizard-step-pill").forEach((el) => {
    el.classList.toggle("active", Number(el.dataset.step) <= n);
  });
}

async function handleFile(file) {
  const tableType = document.getElementById("import-table-type").value;
  const body = document.getElementById("wizard-body");
  setWizardStep(2);
  body.innerHTML = `<div class="state-box"><div class="spinner" style="margin:0 auto"></div><p style="margin-top:10px">جاري تحليل الأعمدة...</p></div>`;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("table_type", tableType);

  let detected;
  try {
    detected = await apiUpload("/import/detect", formData);
  } catch (e) {
    body.innerHTML = emptyState("تعذّرت قراءة الملف", e.message);
    return;
  }

  renderMappingStep(body, file, tableType, detected);
}

function renderMappingStep(body, file, tableType, detected) {
  const standardFields = IMPORT_STANDARD_FIELDS[tableType];
  body.innerHTML = `
    <p style="margin-bottom:10px;"><strong>${esc(file.name)}</strong> &middot; ${fmtNum(detected.row_count)} صف مكتشف</p>
    <p class="tiny muted" style="margin-bottom:12px;">راجع تحديد الأعمدة أدناه وعدّله إن لزم الأمر.</p>
    <div id="mapping-rows">
      ${detected.columns.map((col) => `
        <div class="mapping-row">
          <span>${esc(col)}</span>
          <select data-raw-col="${esc(col)}">
            <option value="">-- تجاهل --</option>
            ${standardFields.map(([field, label]) => `<option value="${field}" ${detected.suggested_mapping[col] === field ? "selected" : ""}>${label}</option>`).join("")}
          </select>
        </div>`).join("")}
    </div>
    <div style="display:flex;gap:10px;margin-top:16px;">
      <button class="btn btn-primary" id="btn-confirm-mapping">تأكيد وتحليل البيانات</button>
    </div>
    <div id="validation-result" style="margin-top:16px;"></div>`;

  document.getElementById("btn-confirm-mapping").addEventListener("click", async () => {
    setWizardStep(3);
    const mapping = {};
    document.querySelectorAll("#mapping-rows select").forEach((sel) => {
      if (sel.value) mapping[sel.dataset.rawCol] = sel.value;
    });
    const resultBox = document.getElementById("validation-result");
    resultBox.innerHTML = `<div class="state-box"><div class="spinner" style="margin:0 auto"></div><p style="margin-top:10px">جاري التحقق من البيانات...</p></div>`;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("table_type", tableType);
    formData.append("mapping", JSON.stringify(mapping));

    let result;
    try {
      result = await apiUpload("/import/apply", formData);
    } catch (e) {
      resultBox.innerHTML = emptyState("تعذّر التحقق من البيانات", e.message);
      return;
    }

    const r = result.report;
    resultBox.innerHTML = `
      <div class="card">
        <p>✓ ${fmtNum(r.row_count)} rows detected</p>
        ${r.missing_prices ? `<p>⚠ ${r.missing_prices} rows have missing prices</p>` : ""}
        ${r.duplicates ? `<p>⚠ ${r.duplicates} duplicate rows</p>` : ""}
        ${r.invalid_dates ? `<p>⚠ ${r.invalid_dates} rows have an invalid date</p>` : ""}
        <div style="margin-top:14px;">
          <button class="btn btn-primary" id="btn-go-dashboard">عرض النتائج في لوحة التحكم</button>
        </div>
      </div>`;
    setWizardStep(4);
    document.getElementById("btn-go-dashboard").addEventListener("click", () => navigate("dashboard"));
  });
}
